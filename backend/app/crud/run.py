"""CRUD das execuções versionadas da análise (V2 T02, §7.2).

Transações curtas, lock otimista por ``version`` e publicação
idempotente: tentativa antiga nunca substitui tentativa mais recente
nem execução cancelada.
"""

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.models.review_event import ReviewEvent
from app.models.source_reference import SourceReference


class VersionConflictError(Exception):
    """Publicação com versão obsoleta ou sobre execução encerrada."""

    code = "VERSION_CONFLICT"


def create_run(
    db: Session,
    *,
    user_id: UUID | str,
    document_id: UUID | str | None = None,
    idempotency_key: str | None = None,
    snapshot: dict | None = None,
) -> AnalysisRun:
    """Cria uma execução; chave repetida retorna a existente (idempotente)."""
    if idempotency_key:
        existing = (
            db.query(AnalysisRun)
            .filter(
                AnalysisRun.user_id == user_id,
                AnalysisRun.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing is not None:
            return existing
    run = AnalysisRun(
        user_id=user_id,
        document_id=document_id,
        status=AnalysisRun.QUEUED,
        idempotency_key=idempotency_key,
        snapshot=snapshot,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run_for_user(
    db: Session, *, run_id: UUID | str, user_id: UUID | str
) -> AnalysisRun | None:
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == run_id, AnalysisRun.user_id == user_id)
        .first()
    )


def list_runs_for_document(
    db: Session, *, document_id: UUID | str, user_id: UUID | str
) -> list[AnalysisRun]:
    """Todas as execuções de um documento — reanálises coexistem (§7)."""
    return (
        db.query(AnalysisRun)
        .filter(
            AnalysisRun.document_id == document_id,
            AnalysisRun.user_id == user_id,
        )
        .order_by(AnalysisRun.created_at)
        .all()
    )


def transition_run(
    db: Session,
    *,
    run: AnalysisRun,
    status: str,
    stage: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AnalysisRun:
    """Avança status/stage; terminal nunca regride para ativo."""
    if run.status in AnalysisRun.TERMINAL_STATUSES and status not in (
        AnalysisRun.TERMINAL_STATUSES
    ):
        raise VersionConflictError(
            f"run {run.id} já encerrado em {run.status}"
        )
    run.status = status
    if stage is not None:
        run.stage = stage
    run.error_code = error_code
    run.error_message = error_message
    if status in AnalysisRun.TERMINAL_STATUSES:
        run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def cancel_run(db: Session, *, run: AnalysisRun) -> AnalysisRun:
    """Cancelamento idempotente; não publica resultado tardio (§7)."""
    if run.status in AnalysisRun.TERMINAL_STATUSES:
        return run
    run.status = AnalysisRun.CANCELLED
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def _content_hash(content: dict | None) -> str | None:
    if content is None:
        return None
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def publish_artifact(
    db: Session,
    *,
    run: AnalysisRun,
    content: dict,
    status: str = "partial",
    quality_notes: dict | list | None = None,
    expected_version: int | None = None,
) -> AnalysisArtifact:
    """Publica o artefato e move o ponteiro em transação curta (§7.2).

    Bloqueia: versão obsoleta, execução cancelada/encerrada por outra
    tentativa (publicação tardia) e segunda publicação do mesmo run.
    """
    if expected_version is not None and run.version != expected_version:
        raise VersionConflictError(
            f"run {run.id} na versão {run.version}, esperado {expected_version}"
        )
    if run.status == AnalysisRun.CANCELLED:
        raise VersionConflictError(f"run {run.id} cancelado; sem publicação tardia")
    if run.published_artifact_id is not None:
        raise VersionConflictError(f"run {run.id} já publicou artefato")
    artifact = AnalysisArtifact(
        run_id=run.id,
        user_id=run.user_id,
        schema_version="2.0",
        status=status,
        review_status=AnalysisArtifact.REVIEW_PENDING,
        content=content,
        content_hash=_content_hash(content),
        quality_notes=quality_notes,
        published_at=datetime.now(timezone.utc),
    )
    db.add(artifact)
    db.flush()
    run.published_artifact_id = artifact.id
    run.status = (
        AnalysisRun.COMPLETED if status == "completed" else AnalysisRun.PARTIAL
    )
    run.completed_at = datetime.now(timezone.utc)
    run.version = run.version + 1
    db.commit()
    db.refresh(artifact)
    db.refresh(run)
    return artifact


def get_published_artifact(
    db: Session, *, run: AnalysisRun
) -> AnalysisArtifact | None:
    if run.published_artifact_id is None:
        return None
    return (
        db.query(AnalysisArtifact)
        .filter(
            AnalysisArtifact.id == run.published_artifact_id,
            AnalysisArtifact.user_id == run.user_id,
        )
        .first()
    )


def add_source_reference(
    db: Session,
    *,
    run: AnalysisRun,
    kind: str = SourceReference.KIND_DOCUMENT,
    revision_id: str | None = None,
    page_number: int | None = None,
    block_id: str | None = None,
    quote: str | None = None,
    url: str | None = None,
    verification_status: str = SourceReference.VERIFICATION_UNVERIFIED,
    content_hash: str | None = None,
    extra: dict | None = None,
) -> SourceReference:
    ref = SourceReference(
        run_id=run.id,
        user_id=run.user_id,
        kind=kind,
        revision_id=revision_id,
        page_number=page_number,
        block_id=block_id,
        quote=quote,
        url=url,
        verification_status=verification_status,
        content_hash=content_hash,
        extra=extra,
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


def add_review_event(
    db: Session,
    *,
    artifact: AnalysisArtifact,
    reviewer_id: UUID | str,
    target: str = "artifact",
    before: dict | None = None,
    after: dict | None = None,
    reason: str | None = None,
) -> ReviewEvent:
    event = ReviewEvent(
        artifact_id=artifact.id,
        reviewer_id=reviewer_id,
        target=target,
        before=before,
        after=after,
        reason=reason,
        source_version=artifact.schema_version,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

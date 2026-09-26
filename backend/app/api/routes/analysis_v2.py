"""API V2 do dossiê jurídico verificável (T11, §14).

Runs versionados, artefato com ETag, seções paginadas, fontes com
autorização, revisão humana com conflito 409 e erros normalizados
{code, stage, retryable, user_message, correlation_id} — sem prompt,
documento ou chave no erro.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import run as run_crud
from app.crud.document import get_document_for_user
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.models.source_reference import SourceReference
from app.models.user import User
from app.schemas.analysis_v2 import (
    ArtifactResponse,
    CreateRunRequest,
    CreateRunResponse,
    ErrorEnvelope,
    ExportRequest,
    ExportResponse,
    ReviewEventRequest,
    ReviewEventResponse,
    RunStatusResponse,
    SectionResponse,
    SourceResponse,
)

router = APIRouter()

STAGE_ORDER = [
    AnalysisRun.STAGE_EXTRACTION,
    AnalysisRun.STAGE_CLASSIFICATION,
    AnalysisRun.STAGE_STRUCTURED_EXTRACTION,
    AnalysisRun.STAGE_RECONCILIATION,
    AnalysisRun.STAGE_RESEARCH,
    AnalysisRun.STAGE_CALCULATIONS,
    AnalysisRun.STAGE_VERIFICATION,
    AnalysisRun.STAGE_COMPOSITION,
]

LIST_SECTIONS = {
    "claims", "facts", "evidence", "legal_references", "theses",
    "calculations", "risks", "sources", "limitations",
}


def _error(status_code: int, code: str, user_message: str, **extra) -> HTTPException:
    envelope = ErrorEnvelope(
        code=code,
        stage=extra.get("stage"),
        retryable=extra.get("retryable", False),
        user_message=user_message,
        correlation_id=str(uuid.uuid4()),
    )
    detail = envelope.model_dump()
    detail.update({k: v for k, v in extra.items() if k not in detail})
    return HTTPException(status_code=status_code, detail=detail)


def _progress(run: AnalysisRun) -> int:
    if run.status in (AnalysisRun.COMPLETED, AnalysisRun.PARTIAL):
        return 100
    if run.status in (AnalysisRun.FAILED, AnalysisRun.CANCELLED):
        return 0
    if run.stage in STAGE_ORDER:
        index = STAGE_ORDER.index(run.stage)
        return 5 + int(90 * index / len(STAGE_ORDER))
    return 5


def _stages(run: AnalysisRun) -> list[dict]:
    current = STAGE_ORDER.index(run.stage) if run.stage in STAGE_ORDER else -1
    return [
        {"stage": stage, "done": i <= current if run.status not in (
            AnalysisRun.FAILED, AnalysisRun.CANCELLED) else False}
        for i, stage in enumerate(STAGE_ORDER)
    ]


def _owned_run(db: Session, run_id: uuid.UUID, user: User) -> AnalysisRun:
    run = run_crud.get_run_for_user(db, run_id=run_id, user_id=user.id)
    if run is None:
        raise _error(404, "NOT_FOUND", "Execução não encontrada.")
    return run


def _owned_artifact(db: Session, artifact_id: uuid.UUID, user: User) -> AnalysisArtifact:
    artifact = (
        db.query(AnalysisArtifact)
        .filter(AnalysisArtifact.id == artifact_id, AnalysisArtifact.user_id == user.id)
        .first()
    )
    if artifact is None:
        raise _error(404, "NOT_FOUND", "Análise não encontrada.")
    return artifact


def _artifact_payload(artifact: AnalysisArtifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=artifact.id,
        run_id=artifact.run_id,
        schema_version=artifact.schema_version,
        status=artifact.status,
        review_status=artifact.review_status,
        content=artifact.content or {},
        content_hash=artifact.content_hash,
        quality_notes=artifact.quality_notes,
        published_at=artifact.published_at,
    )


@router.post("/analysis-runs", response_model=CreateRunResponse, status_code=202)
def create_analysis_run(
    payload: CreateRunRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Cria execução sobre snapshot explícito; chave repetida é idempotente."""
    documents = []
    for document_id in payload.document_ids:
        document = get_document_for_user(
            db, id=document_id, user_id=current_user.id
        )
        if document is None:
            raise _error(404, "NOT_FOUND", "Documento não encontrado ou sem acesso.")
        documents.append(document)
    key = payload.idempotency_key or f"doc:{payload.document_ids[0]}:{payload.module_id}"
    run = run_crud.create_run(
        db,
        user_id=current_user.id,
        document_id=documents[0].id,
        idempotency_key=key,
        snapshot={
            "document_ids": [str(d.id) for d in documents],
            "represented_side": payload.represented_side,
            "objective": payload.objective,
            "reference_date": payload.reference_date,
            "module_id": payload.module_id,
        },
    )
    return CreateRunResponse(
        run_id=run.id, status_url=f"/api/v2/analysis-runs/{run.id}", status=run.status
    )


@router.get("/analysis-runs", response_model=list[RunStatusResponse])
def list_analysis_runs(
    document_id: uuid.UUID | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Lista execuções (filtro opcional por documento) — reanálises coexistem."""
    query = db.query(AnalysisRun).filter(AnalysisRun.user_id == current_user.id)
    if document_id is not None:
        query = query.filter(AnalysisRun.document_id == document_id)
    runs = query.order_by(AnalysisRun.created_at.desc()).limit(50).all()
    return [_run_status(run) for run in runs]


def _run_status(run: AnalysisRun) -> RunStatusResponse:
    return RunStatusResponse(
        run_id=run.id,
        status=run.status,
        stage=run.stage,
        progress=_progress(run),
        version=run.version or 1,
        stages=_stages(run),
        error_code=run.error_code,
        error_message=run.error_message,
        artifact_id=run.published_artifact_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
    )


@router.get("/analysis-runs/{run_id}", response_model=RunStatusResponse)
def get_analysis_run(
    run_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return _run_status(_owned_run(db, run_id, current_user))


@router.post("/analysis-runs/{run_id}/cancel", response_model=RunStatusResponse)
def cancel_analysis_run(
    run_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Cancelamento idempotente; impede publicação tardia."""
    run = _owned_run(db, run_id, current_user)
    return _run_status(run_crud.cancel_run(db, run=run))


@router.get("/analyses/{artifact_id}", response_model=ArtifactResponse)
def get_analysis(
    artifact_id: uuid.UUID,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Artefato versionado com ETag; If-None-Match → 304."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    etag = f'"{artifact.content_hash or artifact.id}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)
    payload = _artifact_payload(artifact)
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        headers={"ETag": etag},
    )


@router.get("/analyses/{artifact_id}/sections/{section}", response_model=SectionResponse)
def get_analysis_section(
    artifact_id: uuid.UUID,
    section: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Seção paginada para conjuntos grandes (§12: sem leitura linear)."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    content = artifact.content or {}
    if section == "overview":
        return SectionResponse(
            section=section, total=1, page=1, page_size=1,
            items=[{
                "scope": content.get("scope", {}),
                "coverage": content.get("coverage", {}),
                "status": artifact.status,
                "review_status": artifact.review_status,
            }],
        )
    if section not in LIST_SECTIONS:
        raise _error(404, "NOT_FOUND", f"Seção desconhecida: {section}.")
    items = content.get(section, []) or []
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size
    return SectionResponse(
        section=section, total=len(items), page=page, page_size=page_size,
        items=items[start : start + page_size],
    )


@router.post("/analyses/{artifact_id}/reanalyze", response_model=CreateRunResponse, status_code=202)
def reanalyze(
    artifact_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Nova execução sobre o mesmo escopo; nunca sobrescreve o original."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == artifact.run_id, AnalysisRun.user_id == current_user.id)
        .first()
    )
    if run is None:
        raise _error(404, "NOT_FOUND", "Execução de origem não encontrada.")
    snapshot = dict(run.snapshot or {})
    new_run = run_crud.create_run(
        db,
        user_id=current_user.id,
        document_id=run.document_id,
        idempotency_key=f"reanalyze:{artifact.id}:{uuid.uuid4().hex[:8]}",
        snapshot={**snapshot, "reanalysis_of": str(artifact.id)},
    )
    return CreateRunResponse(
        run_id=new_run.id,
        status_url=f"/api/v2/analysis-runs/{new_run.id}",
        status=new_run.status,
    )


@router.get("/analyses/{artifact_id}/sources", response_model=list[SourceResponse])
def list_artifact_sources(
    artifact_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Fontes do artefato com autorização; resolve documento+página."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    refs = (
        db.query(SourceReference)
        .filter(SourceReference.run_id == artifact.run_id,
                SourceReference.user_id == current_user.id)
        .order_by(SourceReference.page_number, SourceReference.created_at)
        .all()
    )
    run = db.query(AnalysisRun).filter(AnalysisRun.id == artifact.run_id).first()
    return [
        SourceResponse(
            id=ref.id, kind=ref.kind, revision_id=ref.revision_id,
            page_number=ref.page_number, block_id=ref.block_id, quote=ref.quote,
            url=ref.url, verification_status=ref.verification_status,
            document_id=run.document_id if run else None,
        )
        for ref in refs
    ]


@router.get("/sources/{source_id}", response_model=SourceResponse)
def resolve_source(
    source_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Resolve fonte com autorização e localizador (1 clique, §12)."""
    ref = (
        db.query(SourceReference)
        .filter(SourceReference.id == source_id,
                SourceReference.user_id == current_user.id)
        .first()
    )
    if ref is None:
        raise _error(404, "NOT_FOUND", "Fonte não encontrada.")
    run = db.query(AnalysisRun).filter(AnalysisRun.id == ref.run_id).first()
    return SourceResponse(
        id=ref.id, kind=ref.kind, revision_id=ref.revision_id,
        page_number=ref.page_number, block_id=ref.block_id, quote=ref.quote,
        url=ref.url, verification_status=ref.verification_status,
        document_id=run.document_id if run else None,
    )


@router.post("/analyses/{artifact_id}/review-events", response_model=ReviewEventResponse, status_code=201)
def create_review_event(
    artifact_id: uuid.UUID,
    payload: ReviewEventRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Correção/decisão com versão esperada; conflito → 409."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    run = db.query(AnalysisRun).filter(AnalysisRun.id == artifact.run_id).first()
    current_version = run.version if run else 1
    if payload.expected_version is not None and payload.expected_version != current_version:
        raise _error(
            409, "VERSION_CONFLICT",
            "Artefato alterado por outra revisão; recarregue e reaplique.",
            retryable=False,
        )
    event = run_crud.add_review_event(
        db, artifact=artifact, reviewer_id=current_user.id,
        target=payload.target, before=payload.before, after=payload.after,
        reason=payload.reason,
    )
    return ReviewEventResponse(
        id=event.id, target=event.target, reason=event.reason,
        source_version=event.source_version, created_at=event.created_at,
    )


@router.get("/analyses/{artifact_id}/review-events", response_model=list[ReviewEventResponse])
def list_review_events(
    artifact_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Histórico de revisão: saída original e autoria preservadas."""
    from app.models.review_event import ReviewEvent

    artifact = _owned_artifact(db, artifact_id, current_user)
    events = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.artifact_id == artifact.id)
        .order_by(ReviewEvent.created_at)
        .all()
    )
    return [
        ReviewEventResponse(
            id=e.id, target=e.target, reason=e.reason,
            source_version=e.source_version, created_at=e.created_at,
        )
        for e in events
    ]


def _export_job_id(artifact: AnalysisArtifact, mode: str) -> str:
    seed = f"{artifact.id}:{mode}:{artifact.content_hash or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


@router.post("/analyses/{artifact_id}/exports", response_model=ExportResponse, status_code=202)
def request_export(
    artifact_id: uuid.UUID,
    payload: ExportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Relatório vinculado à revisão; mesmo artefato, sem nova IA."""
    from app.core.v2_export import MODE_COMPLETE, MODE_EXECUTIVE

    mode = payload.mode if payload.mode in (MODE_EXECUTIVE, MODE_COMPLETE) else MODE_COMPLETE
    artifact = _owned_artifact(db, artifact_id, current_user)
    job_id = _export_job_id(artifact, mode)
    return ExportResponse(
        job_id=job_id,
        download_url=f"/api/v2/exports/{job_id}?artifact_id={artifact.id}&mode={mode}",
        mode=mode,
    )


@router.get("/exports/{job_id}")
def download_export(
    job_id: str,
    artifact_id: uuid.UUID,
    mode: str = "complete",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Regenera deterministicamente o relatório do artefato (job sem estado)."""
    from app.core.v2_export import MODE_COMPLETE, MODE_EXECUTIVE, build_report
    from app.models.review_event import ReviewEvent
    from fastapi.responses import PlainTextResponse

    artifact = _owned_artifact(db, artifact_id, current_user)
    mode = mode if mode in (MODE_EXECUTIVE, MODE_COMPLETE) else MODE_COMPLETE
    if _export_job_id(artifact, mode) != job_id:
        raise _error(404, "NOT_FOUND", "Exportação não encontrada.")
    refs = (
        db.query(SourceReference)
        .filter(SourceReference.run_id == artifact.run_id,
                SourceReference.user_id == current_user.id)
        .all()
    )
    events = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.artifact_id == artifact.id)
        .order_by(ReviewEvent.created_at)
        .all()
    )
    body = build_report(
        artifact.content or {},
        mode=mode,
        sources=[{"id": str(r.id), "page_number": r.page_number,
                  "quote": r.quote, "verification_status": r.verification_status}
                 for r in refs],
        review_events=[{"target": e.target, "reason": e.reason} for e in events],
        artifact_status=artifact.status,
        review_status=artifact.review_status,
    )
    return PlainTextResponse(
        body,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="dossie-{job_id}.md"'},
    )

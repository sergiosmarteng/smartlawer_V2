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
from app.core.pipeline.contracts import PIPELINE_STAGES, calculate_progress
from app.crud import run as run_crud
from app.crud.document import get_document_for_user
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.models.source_reference import SourceReference
from app.models.user import User
from app.schemas.analysis_v2 import (
    ArtifactResponse,
    AttachDocumentRequest,
    CaseCreateRequest,
    CaseResponse,
    CompareResponse,
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
    VersionResponse,
    VisualResponse,
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


def _progress(run: AnalysisRun, stage_runs=None) -> int:
    """Progresso da API V2 (Onda 0 Task 3: honesto por construção).

    ``STAGE_ORDER`` (8 etapas V2) é preservado para compatibilidade da API.
    O pipeline V3 usa ``PIPELINE_STAGES`` (12 etapas) via
    ``calculate_progress`` quando ``stage_runs`` são fornecidos. Em ambos
    os casos, ``extraction`` nunca retorna 100% (defeito §3.1 do spec).
    """
    if stage_runs is not None:
        return calculate_progress(run, stage_runs).percent
    if run.stage == AnalysisRun.STAGE_EXTRACTION:
        if run.status in (AnalysisRun.FAILED, AnalysisRun.CANCELLED):
            return 0
        # Extração em andamento ou terminal sem publicação: nunca 100%.
        if run.status in (AnalysisRun.COMPLETED, AnalysisRun.PARTIAL):
            return 95
        if run.stage in STAGE_ORDER:
            index = STAGE_ORDER.index(run.stage)
            return min(5 + int(90 * index / len(STAGE_ORDER)), 95)
        return 5
    if run.status in (AnalysisRun.COMPLETED, AnalysisRun.PARTIAL):
        return 100
    if run.status in (AnalysisRun.FAILED, AnalysisRun.CANCELLED):
        return 0
    if run.stage in STAGE_ORDER:
        index = STAGE_ORDER.index(run.stage)
        return 5 + int(90 * index / len(STAGE_ORDER))
    # Estágios V3 fora da ordem V2: deriva de PIPELINE_STAGES sem 100 fictício.
    if run.stage in PIPELINE_STAGES:
        index = PIPELINE_STAGES.index(run.stage)
        return min(5 + int(90 * index / len(PIPELINE_STAGES)), 99)
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
    is_legacy = (artifact.schema_version or "") != "3.0"
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
        legacy=is_legacy,
        reanalyze_available=is_legacy,
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
            "case_id": str(payload.case_id) if payload.case_id else None,
            "represented_side": payload.represented_side,
            "objective": payload.objective,
            "reference_date": payload.reference_date,
            "area_overrides": list(payload.area_overrides or []),
            "module_id": payload.module_id,
        },
    )
    if payload.case_id is not None:
        run.case_id = payload.case_id
        db.commit()
        db.refresh(run)
    return CreateRunResponse(
        run_id=run.id, status_url=f"/api/v2/analysis-runs/{run.id}", status=run.status
    )


@router.get("/analysis-runs", response_model=list[RunStatusResponse])
def list_analysis_runs(
    document_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Lista execuções (filtros por documento e/ou caso) — reanálises coexistem."""
    query = db.query(AnalysisRun).filter(AnalysisRun.user_id == current_user.id)
    if document_id is not None:
        query = query.filter(AnalysisRun.document_id == document_id)
    if case_id is not None:
        query = query.filter(AnalysisRun.case_id == case_id)
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


def _owned_case(db: Session, case_id: uuid.UUID, user: User):
    from app.models.case import Case

    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.user_id == user.id)
        .first()
    )
    if case is None:
        raise _error(404, "NOT_FOUND", "Caso não encontrado.")
    return case


def _case_payload(db: Session, case) -> CaseResponse:
    from app.models.case import CaseDocument

    links = (
        db.query(CaseDocument)
        .filter(CaseDocument.case_id == case.id)
        .order_by(CaseDocument.added_at)
        .all()
    )
    return CaseResponse(
        id=case.id,
        name=case.name,
        area=case.area,
        documents=[
            {"document_id": link.document_id, "role": link.role} for link in links
        ],
        created_at=case.created_at,
    )


@router.post("/cases", response_model=CaseResponse, status_code=201)
def create_case(
    payload: CaseCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Cria um caso para agrupar documentos do mesmo assunto."""
    from app.crud.case import create_case as _create_case

    case = _create_case(
        db, user_id=current_user.id, name=payload.name,
        area=payload.area, description=payload.description,
    )
    return _case_payload(db, case)


@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return _case_payload(db, _owned_case(db, case_id, current_user))


@router.post("/cases/{case_id}/documents", status_code=201)
def attach_case_document(
    case_id: uuid.UUID,
    payload: AttachDocumentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Anexa documento próprio ao caso; documento alheio → 404 opaco."""
    from app.crud.case import CaseAccessError, attach_document

    case = _owned_case(db, case_id, current_user)
    document = get_document_for_user(
        db, id=payload.document_id, user_id=current_user.id
    )
    if document is None:
        raise _error(404, "NOT_FOUND", "Documento não encontrado ou sem acesso.")
    try:
        link = attach_document(db, case=case, document=document, role=payload.role)
    except CaseAccessError:
        raise _error(404, "NOT_FOUND", "Documento não encontrado ou sem acesso.")
    return {"case_id": str(case.id), "document_id": str(link.document_id)}


@router.get("/analyses/{artifact_id}/visuals", response_model=list[VisualResponse])
def list_artifact_visuals(
    artifact_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Galeria visual: chaves opacas, nunca caminho interno."""
    artifact = _owned_artifact(db, artifact_id, current_user)
    visuals = (artifact.content or {}).get("visuals", []) or []
    return [
        VisualResponse(
            id=str(v.get("id")),
            page_number=v.get("page_number"),
            kind=v.get("kind"),
            storage_key=v.get("storage_key"),
            thumbnail_key=v.get("thumbnail_key"),
        )
        for v in visuals
    ]


def _versions_for_artifact(db: Session, artifact: AnalysisArtifact) -> list[AnalysisArtifact]:
    run = db.query(AnalysisRun).filter(AnalysisRun.id == artifact.run_id).first()
    if run is None:
        return [artifact]
    query = db.query(AnalysisArtifact).filter(AnalysisArtifact.user_id == artifact.user_id)
    if run.document_id is not None:
        peer_run_ids = [
            r.id for r in db.query(AnalysisRun).filter(
                AnalysisRun.user_id == artifact.user_id,
                AnalysisRun.document_id == run.document_id,
            ).all()
        ]
        if peer_run_ids:
            query = query.filter(AnalysisArtifact.run_id.in_(peer_run_ids))
    return query.order_by(AnalysisArtifact.created_at).all()


@router.get("/analyses/{artifact_id}/versions", response_model=list[VersionResponse])
def list_artifact_versions(
    artifact_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    artifact = _owned_artifact(db, artifact_id, current_user)
    return [
        VersionResponse(
            id=v.id, run_id=v.run_id, schema_version=v.schema_version,
            status=v.status, created_at=v.created_at,
        )
        for v in _versions_for_artifact(db, artifact)
    ]


@router.get("/analyses/{artifact_id}/compare", response_model=CompareResponse)
def compare_artifacts(
    artifact_id: uuid.UUID,
    against: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Compara artefatos por IDs estáveis de pedidos."""
    after = _owned_artifact(db, artifact_id, current_user)
    before = _owned_artifact(db, against, current_user)

    def _claim_ids(artifact: AnalysisArtifact) -> dict[str, dict]:
        return {
            str(c.get("id")): c
            for c in ((artifact.content or {}).get("claims", []) or [])
            if c.get("id")
        }

    before_claims, after_claims = _claim_ids(before), _claim_ids(after)
    added = sorted(set(after_claims) - set(before_claims))
    removed = sorted(set(before_claims) - set(after_claims))
    changed = sorted(
        cid for cid in set(before_claims) & set(after_claims)
        if before_claims[cid] != after_claims[cid]
    )
    return CompareResponse(
        before_id=before.id, after_id=after.id,
        added=added, removed=removed, changed=changed,
    )


@router.post("/analysis-runs/{run_id}/resume", response_model=RunStatusResponse, status_code=202)
def resume_analysis_run(
    run_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Retoma execução interrompida; só ``failed`` sem artefato é retomável."""
    run = _owned_run(db, run_id, current_user)
    try:
        resumed = run_crud.resume_run(db, run=run)
    except run_crud.VersionConflictError:
        raise _error(
            409, "NOT_RESUMABLE", "Execução não está em estado retomável.",
            retryable=False,
        )
    return _run_status(resumed)

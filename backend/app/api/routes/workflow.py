from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.api.routes.templates import generate_docx_document
from app.crud.document import get_document_for_user, get_documents_by_user
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.user import User
from app.schemas.workflow import (
    AnalysisDetailResponse,
    ProcessResponse,
    TaskStatusResponse,
)

router = APIRouter()


def _normalize_status(document_status: str | None) -> str:
    mapping = {
        Document.STATUS_UPLOADED: "PENDING",
        Document.STATUS_PROCESSING: "PROCESSING",
        Document.STATUS_COMPLETED: "COMPLETED",
        Document.STATUS_ERROR: "FAILED",
    }
    return mapping.get((document_status or "").lower(), "PENDING")


def _analysis_url(analysis: Analysis | None) -> str | None:
    return f"/analysis/{analysis.id}" if analysis else None


def _docx_download_url(analysis: Analysis | None) -> str | None:
    return f"/analysis/{analysis.id}/docx" if analysis else None


def _progress_for_document(document: Document) -> int:
    normalized = _normalize_status(document.status)
    if normalized == "COMPLETED":
        return 100
    if normalized == "FAILED":
        return 0

    detail = (document.status_detail or "").lower()
    if "extract" in detail:
        return 35
    if "analysis" in detail or "fallback" in detail:
        return 75
    if "retry" in detail:
        return 50
    return 15


def _resolve_analysis_by_identifier(
    db: Session,
    *,
    identifier: UUID,
    current_user: User,
) -> tuple[Analysis | None, Document | None]:
    analysis = (
        db.query(Analysis)
        .options(selectinload(Analysis.document))
        .join(Document, Analysis.document_id == Document.id)
        .filter(Analysis.id == identifier, Document.user_id == current_user.id)
        .first()
    )
    if analysis:
        return analysis, analysis.document

    document = get_document_for_user(
        db,
        id=identifier,
        user_id=current_user.id,
        load_analysis=True,
    )
    if document and document.analysis:
        return document.analysis, document

    return None, document


def _analysis_payload(analysis: Analysis) -> AnalysisDetailResponse:
    defense_items = analysis.defense_theses or []
    generated_defense = "\n\n".join(
        f"{index + 1}. {item}" for index, item in enumerate(defense_items)
    )
    document = analysis.document

    return AnalysisDetailResponse(
        id=analysis.id,
        document_id=document.id,
        documentName=document.filename,
        title=document.filename,
        summary=analysis.summary or "",
        keyArguments=analysis.requests or [],
        requests=analysis.requests or [],
        laws=analysis.laws or [],
        evidence=analysis.evidence,
        defense_theses=defense_items,
        status=_normalize_status(document.status),
        status_detail=document.status_detail,
        created_at=analysis.created_at or document.uploaded_at,
        completed_at=document.completed_at,
        generatedDefenseStrategy=generated_defense,
        docxDownloadUrl=_docx_download_url(analysis),
    )


@router.get("/processes", response_model=list[ProcessResponse])
def list_processes(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    documents = get_documents_by_user(
        db,
        user_id=current_user.id,
        load_analysis=True,
    )
    return [
        ProcessResponse(
            id=doc.id,
            analysis_id=doc.analysis.id if doc.analysis else None,
            title=doc.filename,
            status=_normalize_status(doc.status),
            created_at=doc.uploaded_at,
            updated_at=doc.updated_at,
            completed_at=doc.completed_at,
            status_detail=doc.status_detail,
            analysis_url=_analysis_url(doc.analysis),
            docxDownloadUrl=_docx_download_url(doc.analysis),
        )
        for doc in documents
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Poll the processing pipeline of a document.

    Workflow identity rule (BL-014, codified): ``task_id`` IS the
    document id — one document owns exactly one pipeline. Cross-user
    lookups return 404 (no existence oracle).
    """
    document = get_document_for_user(
        db,
        id=task_id,
        user_id=current_user.id,
        load_analysis=True,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Task not found")

    analysis = document.analysis

    return TaskStatusResponse(
        task_id=document.id,
        document_id=document.id,
        title=document.filename,
        status=_normalize_status(document.status),
        progress=_progress_for_document(document),
        analysis_id=analysis.id if analysis else None,
        status_detail=document.status_detail,
        error_message=document.error_message,
        created_at=document.uploaded_at,
        updated_at=document.updated_at,
        completed_at=document.completed_at,
        analysis_url=_analysis_url(analysis),
        docxDownloadUrl=_docx_download_url(analysis),
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis_result(
    analysis_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    analysis, document = _resolve_analysis_by_identifier(
        db,
        identifier=analysis_id,
        current_user=current_user,
    )
    if not analysis:
        if document:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Analysis not ready",
                    "task_id": str(document.id),
                    "status": _normalize_status(document.status),
                    "status_detail": document.status_detail,
                },
            )
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _analysis_payload(analysis)


@router.get("/analysis/{analysis_id}/docx")
def download_analysis_docx(
    analysis_id: UUID,
    template_id: UUID | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return generate_docx_document(
        analysis_id=analysis_id,
        template_id=template_id,
        db=db,
        current_user=current_user,
    )

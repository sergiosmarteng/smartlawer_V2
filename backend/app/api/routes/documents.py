import os
import shutil
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.document import create_document, get_documents_by_user, update_document_state
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentResponse
from app.schemas.workflow import BatchUploadError, BatchUploadResponse, UploadSubmissionResponse
from app.tasks.document_tasks import process_pdf_task

router = APIRouter()

MAX_BATCH_FILES = 10

UPLOAD_DIRECTORY = (
    "/data/uploads"
    if os.environ.get("ENVIRONMENT") != "development_local"
    else "./uploads"
)

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


def _normalize_document_status(status: str | None) -> str:
    mapping = {
        Document.STATUS_UPLOADED: "PENDING",
        Document.STATUS_PROCESSING: "PROCESSING",
        Document.STATUS_COMPLETED: "COMPLETED",
        Document.STATUS_ERROR: "FAILED",
    }
    return mapping.get((status or "").lower(), "PENDING")


@router.post("/upload", response_model=UploadSubmissionResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Upload a PDF and queue its processing pipeline.

    Workflow identity rule (BL-014, codified): one document owns exactly
    one processing pipeline, so ``task_id == document id == id`` by
    design (a document has at most one ``Analysis``). ``taskStatusUrl``
    is the canonical polling URL, relative to the API root (``/api/v1``).
    """
    return _store_and_queue(db, current_user, file)


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Upload up to ``MAX_BATCH_FILES`` PDFs in one call (C3/BL-021).

    Per-file tolerance: a rejected file lands in ``errors`` without
    failing the accepted ones. Each accepted file queues its own
    pipeline and is monitored through the usual dashboard/task flow.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"At most {MAX_BATCH_FILES} files per batch",
        )

    items: list[UploadSubmissionResponse] = []
    errors: list[BatchUploadError] = []
    for file in files:
        try:
            items.append(_store_and_queue(db, current_user, file))
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Upload failed"
            errors.append(
                BatchUploadError(filename=file.filename or "unknown", detail=detail)
            )
    return BatchUploadResponse(items=items, errors=errors)


def _store_and_queue(
    db: Session,
    current_user: User,
    file: UploadFile,
) -> UploadSubmissionResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIRECTORY, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = create_document(
        db,
        DocumentCreate(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            content_type=file.content_type,
        ),
    )

    try:
        process_pdf_task.delay(str(document.id), file_path)
    except Exception as exc:
        update_document_state(
            db,
            id=document.id,
            status=Document.STATUS_ERROR,
            status_detail="Unable to queue background processing",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=503,
            detail="Document upload succeeded, but background processing could not be started.",
        ) from exc

    return UploadSubmissionResponse(
        id=document.id,
        task_id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        content_type=document.content_type,
        status=_normalize_document_status(document.status),
        status_detail=document.status_detail,
        uploaded_at=document.uploaded_at,
        taskStatusUrl=f"/tasks/{document.id}",
        analysis_id=None,
        analysis_url=None,
        docxDownloadUrl=None,
    )


@router.get("/", response_model=List[DocumentResponse])
def get_user_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return get_documents_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.schemas.document import DocumentCreate

UNSET = object()


def create_document(db: Session, obj_in: DocumentCreate) -> Document:
    db_obj = Document(
        user_id=obj_in.user_id,
        filename=obj_in.filename,
        file_path=obj_in.file_path,
        content_type=obj_in.content_type,
        status=Document.STATUS_UPLOADED,
        status_detail="Queued for processing",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_document(db: Session, id: UUID | str) -> Document | None:
    return db.query(Document).filter(Document.id == id).first()


def get_document_for_user(
    db: Session,
    *,
    id: UUID | str,
    user_id: UUID | str,
    load_analysis: bool = False,
) -> Document | None:
    query = db.query(Document)
    if load_analysis:
        query = query.options(selectinload(Document.analysis))
    return query.filter(Document.id == id, Document.user_id == user_id).first()


def get_documents_by_user(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    load_analysis: bool = False,
):
    query = db.query(Document)
    if load_analysis:
        query = query.options(selectinload(Document.analysis))
    return (
        query.filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_document_status(
    db: Session,
    id: UUID | str,
    status: str,
) -> Document | None:
    return update_document_state(db, id=id, status=status)


def update_document_state(
    db: Session,
    id: UUID | str,
    *,
    status: str | None = None,
    status_detail: str | None = None,
    error_message=UNSET,
    completed_at=UNSET,
) -> Document | None:
    document = get_document(db, id)
    if not document:
        return None

    if status is not None:
        document.status = status
    if status_detail is not None:
        document.status_detail = status_detail
    if error_message is not UNSET:
        document.error_message = error_message
    if completed_at is not UNSET:
        document.completed_at = completed_at

    document.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(document)
    return document

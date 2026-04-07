from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate
from uuid import UUID

def create_document(db: Session, obj_in: DocumentCreate) -> Document:
    db_obj = Document(
        user_id=obj_in.user_id,
        filename=obj_in.filename,
        file_path=obj_in.file_path,
        content_type=obj_in.content_type,
        status="uploaded"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_document(db: Session, id: UUID) -> Document:
    return db.query(Document).filter(Document.id == id).first()

def get_documents_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()

def update_document_status(db: Session, id: UUID, status: str) -> Document:
    document = get_document(db, id)
    if document:
        document.status = status
        db.commit()
        db.refresh(document)
    return document

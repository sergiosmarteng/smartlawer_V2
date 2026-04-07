import os
import shutil
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.document import create_document, get_documents_by_user
from app.schemas.document import DocumentResponse, DocumentCreate
from app.models.user import User
from app.tasks.document_tasks import process_pdf_task

router = APIRouter()

# Pasta nativa para uploads via docker volume ou local
UPLOAD_DIRECTORY = "/data/uploads" if os.environ.get("ENVIRONMENT") != "development_local" else "./uploads"

# Se executando local limpo sem docker, cria a pasta se sumir
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Submete um PDF para extração e processamento de background via Celery.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Garante segurança no filename
    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIRECTORY, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Criação estrutural na base (CRUD)
    doc_in = DocumentCreate(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type
    )
    document = create_document(db, doc_in)

    # Dispara background OCR no Celery (delay passará ID e path)
    process_pdf_task.delay(str(document.id), file_path)

    return document

@router.get("/", response_model=List[DocumentResponse])
def get_user_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    return get_documents_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

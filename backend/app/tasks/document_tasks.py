import logging
from app.worker import celery_app
from app.core.database import SessionLocal
from app.crud.document import update_document_status, get_document
from app.core.pdf_processor import PDFExtractor
from app.models.analysis import Analysis

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_pdf_task(self, document_id: str, file_path: str):
    logger.info(f"Iniciando processamento para documento {document_id}")
    db = SessionLocal()
    try:
        # Atualiza status inicial
        update_document_status(db, id=document_id, status="processing")
        
        # Faz uso do PDFExtractor (PyMuPDF + Tesseract)
        raw_text = PDFExtractor.extract_text(file_path=file_path)
        
        # Salva o texto provisoriamente ou liga à tabela Analysis vazia
        # (A fase 4 fará a integração OpenAI nela)
        doc = get_document(db, id=document_id)
        if doc and not doc.analysis:
            analysis = Analysis(document_id=document_id, summary=raw_text[:1000]) # Resumo basico / placeholder
            db.add(analysis)
        
        update_document_status(db, id=document_id, status="completed")
        db.commit()
    except Exception as exc:
        logger.error(f"Erro em process_pdf_task: {exc}")
        update_document_status(db, id=document_id, status="error")
        db.commit()
        # Retry em caso de erro na OCR ou leitura
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()

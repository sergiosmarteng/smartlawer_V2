import logging
from datetime import datetime, timezone

from app.core.ai_engine import LegalAnalyzer
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.docling_extractor import extract_markdown as docling_extract_markdown
from app.core.pdf_processor import PDFExtractor
from app.crud.document import get_document, update_document_state
from app.models.analysis import Analysis
from app.models.document import Document
from app.worker import celery_app

logger = logging.getLogger(__name__)


def prepare_analysis_input(document_id: str, file_path: str, raw_text: str) -> str:
    """Return the text the AI should analyze, persisting extraction outputs.

    Rule (docling-status.md minimum viable integration):
    - Docling success (flag on) -> analyze ``structured_markdown``
    - Docling failure or disabled -> analyze ``raw_text`` from PDFExtractor
    Docling never fails the task: any error means fallback to raw text.
    """
    db = SessionLocal()
    try:
        markdown = None
        if settings.DOCLING_ENABLED:
            update_document_state(
                db,
                id=document_id,
                status=Document.STATUS_PROCESSING,
                status_detail="Converting PDF to structured markdown",
                error_message=None,
            )
            try:
                markdown = docling_extract_markdown(file_path)
            except Exception as exc:
                # The adapter contract is to never raise, but the task
                # must survive even if that contract is ever broken.
                logger.warning(
                    "Docling falhou para %s (%s); usando raw_text.", document_id, exc
                )
                markdown = None

        doc = get_document(db, id=document_id)
        if doc is not None:
            doc.raw_text = raw_text
            doc.structured_markdown = markdown
            db.commit()

        if markdown:
            logger.info("Documento %s: analisando via structured_markdown.", document_id)
            return markdown
        logger.info("Documento %s: analisando via raw_text.", document_id)
        return raw_text
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_pdf_task(self, document_id: str, file_path: str):
    logger.info("Iniciando processamento para documento %s", document_id)
    db = SessionLocal()
    try:
        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_PROCESSING,
            status_detail="Extracting text from PDF",
            error_message=None,
        )

        raw_text = PDFExtractor.extract_text(file_path=file_path)

        analysis_text = prepare_analysis_input(document_id, file_path, raw_text)

        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_PROCESSING,
            status_detail="Generating legal analysis",
            error_message=None,
        )

        analyzer = LegalAnalyzer()
        try:
            ai_data = analyzer.analyze_petition(analysis_text)

            doc = get_document(db, id=document_id)
            if doc and not doc.analysis:
                db.add(
                    Analysis(
                        document_id=document_id,
                        summary=ai_data.get("summary", ""),
                        requests=ai_data.get("requests", []),
                        laws=ai_data.get("laws", []),
                        evidence=ai_data.get("evidence", ""),
                        defense_theses=ai_data.get("defense_theses", []),
                    )
                )
        except Exception as ai_exc:
            logger.error("OpenAI falhou: %s. Processando fallback provisorio.", ai_exc)
            doc = get_document(db, id=document_id)
            if doc and not doc.analysis:
                db.add(Analysis(document_id=document_id, summary=raw_text[:1000]))
            update_document_state(
                db,
                id=document_id,
                status=Document.STATUS_PROCESSING,
                status_detail="AI provider unavailable; using fallback summary",
                error_message=None,
            )

        db.commit()
        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_COMPLETED,
            status_detail="Analysis ready",
            error_message=None,
            completed_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.exception("Erro em process_pdf_task: %s", exc)
        db.rollback()

        if self.request.retries < self.max_retries:
            update_document_state(
                db,
                id=document_id,
                status=Document.STATUS_PROCESSING,
                status_detail=f"Retrying after processing error ({self.request.retries + 1}/{self.max_retries})",
                error_message=str(exc),
            )
            raise self.retry(exc=exc, countdown=30)

        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_ERROR,
            status_detail="Processing failed",
            error_message=str(exc),
        )
        raise
    finally:
        db.close()

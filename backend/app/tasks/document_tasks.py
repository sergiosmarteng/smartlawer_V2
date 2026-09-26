import logging
from datetime import datetime, timezone

from app.core.ai_engine import AnalysisError, LegalAnalyzer
from app.core.analysis_verifier import decide_status, verify
from app.core.audit import audit_document_completion
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.docling_extractor import extract_markdown as docling_extract_markdown
from app.core.docling_extractor import (
    MAX_FIGURES,
    _extract_figures_fitz,
    extract_figures as docling_extract_figures,
)
from app.core.coverage_planner import build_prompt_window
from app.core.extraction import (
    FIGURES_TRUNCATED,
    extract_inventory,
    figures_with_state,
)
from app.core.schemas_v2 import coerce_legacy_analysis
from app.core.storage import figure_directory
from app.core.embeddings import embed_texts
from app.core.legal_chunker import chunk_legal_text
from app.core.pdf_processor import PDFExtractor
from app.crud.document import get_document, update_document_state
from app.crud.extraction import (
    get_or_create_revision,
    replace_source_blocks,
)
from app.crud.figure import replace_document_figures
from app.crud.prompt import get_default_strategy_prompt
from app.crud.run import (
    VersionConflictError,
    create_run,
    publish_artifact,
    transition_run,
)
from app.models.analysis import Analysis
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_revision import DocumentRevision
from app.models.source_block import SourceBlock
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


def index_document_chunks(document_id: str, analysis_text: str) -> int:
    """Chunk + embed *analysis_text* into ``document_chunks`` (V2 T04).

    Idempotent: existing chunks for the document are replaced. Texto
    persiste SEMPRE (busca FTS degradada); vetores só quando íntegros
    (cardinalidade + dimensão + finitos). Retorna chunks armazenados.
    Raises on unexpected errors — the caller must guard the task.
    """
    from app.core.embeddings import embedding_space, validate_vectors

    chunks = chunk_legal_text(analysis_text)
    if not chunks:
        return 0

    contents = [c.content for c in chunks]
    vectors = embed_texts(contents)
    space = embedding_space()
    if not validate_vectors(contents, vectors):
        if vectors is not None:
            logger.warning(
                "Documento %s: vetores inválidos; persistindo só texto (FTS).",
                document_id,
            )
        else:
            logger.warning(
                "Documento %s: embeddings indisponiveis; persistindo só texto (FTS).",
                document_id,
            )
        vectors = [None] * len(chunks)

    db = SessionLocal()
    try:
        doc = get_document(db, id=document_id)
        if doc is None:
            return 0
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).delete()
        for chunk, vector in zip(chunks, vectors):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding=vector,
                    embedding_model=space["model"],
                    embedding_model_version=space["version"],
                    embedding_provider=space["provider"],
                    embedding_dimensions=space["dimensions"],
                )
            )
        db.commit()
        return len(chunks)
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

        # V2 T11: execução versionada do pipeline (best-effort; o legado
        # Document/Analysis continua sendo a projeção compatível).
        run = None
        try:
            doc0 = get_document(db, id=document_id)
            if doc0 is not None:
                run = create_run(
                    db,
                    user_id=doc0.user_id,
                    document_id=doc0.id,
                    idempotency_key=f"pipeline:{document_id}",
                    snapshot={"file_path": file_path},
                )
                transition_run(
                    db, run=run, status=AnalysisRun.RUNNING,
                    stage=AnalysisRun.STAGE_EXTRACTION,
                )
        except Exception as exc:
            logger.warning("Run V2 não criado para %s (%s); seguindo.", document_id, exc)
            run = None

        # V2 T03: inventário página/bloco por revisão (best-effort, nunca
        # derruba a task). Figuras ligadas à revisão, sem novo catálogo.
        revision_id: str | None = None
        try:
            doc = get_document(db, id=document_id)
            if doc is not None:
                with open(file_path, "rb") as handle:
                    file_sha = DocumentRevision.hash_bytes(handle.read())
                revision, _ = get_or_create_revision(
                    db,
                    document_id=doc.id,
                    user_id=doc.user_id,
                    file_sha256=file_sha,
                    origin=file_path,
                )
                revision_id = str(revision.id)
                pages, coverage = extract_inventory(file_path, revision_id)
                if pages:
                    replace_source_blocks(db, revision=revision, pages=pages)
                revision.pages_total = coverage.get("pages_total")
                revision.extra = {"coverage": coverage}
                db.commit()
        except Exception as exc:
            logger.warning(
                "Inventário de extração falhou para %s (%s); seguindo.",
                document_id,
                exc,
            )

        # V2 T05: janela head+tail com cobertura registrada (fim do corte
        # fixo). Textos curtos passam intactos; longos preservam a cauda
        # (rol de pedidos) e registram o omitido na revisão.
        try:
            windowed_text, prompt_coverage = build_prompt_window(analysis_text)
            analysis_text = windowed_text
            if revision_id is not None and prompt_coverage.get("truncated"):
                revision_row = db.get(DocumentRevision, revision_id)
                if revision_row is not None:
                    extra = dict(revision_row.extra or {})
                    extra["prompt_coverage"] = prompt_coverage
                    revision_row.extra = extra
                    db.commit()
        except Exception as exc:
            logger.warning(
                "Janela de cobertura falhou para %s (%s); usando texto integral.",
                document_id,
                exc,
            )

        try:
            doc = get_document(db, id=document_id)
            if doc is not None:
                if settings.DOCLING_ENABLED:
                    figures = docling_extract_figures(
                        file_path, figure_directory(str(document_id))
                    )
                else:
                    figures = _extract_figures_fitz(
                        file_path, figure_directory(str(document_id))
                    )
                truncated = len(figures) >= MAX_FIGURES
                figures, figures_state = figures_with_state(
                    figures, truncated=truncated
                )
                if revision_id is not None and figures_state == "ok_empty":
                    # Checagem independente: inventário viu imagens mas
                    # nenhuma figura foi extraída → lacuna, não "sem figuras".
                    try:
                        imaged = [
                            b
                            for b in db.query(SourceBlock)
                            .filter(SourceBlock.revision_id == revision_id)
                            .all()
                            if b.block_type == "image"
                        ]
                        if imaged:
                            figures_state = "figures_unresolved"
                    except Exception:
                        pass
                if revision_id is not None:
                    try:
                        owner = get_document(db, id=document_id)
                        if owner is not None:
                            revision_row = db.get(DocumentRevision, revision_id)
                            if revision_row is not None:
                                extra = dict(revision_row.extra or {})
                                extra["figures_state"] = figures_state
                                revision_row.extra = extra
                                db.commit()
                    except Exception:
                        pass
                replace_document_figures(
                    db,
                    document_id=doc.id,
                    user_id=doc.user_id,
                    figures=figures,
                    revision_id=revision_id,
                )
                logger.info(
                    "Documento %s: %d figura(s) extraída(s) (docling=%s).",
                    document_id,
                    len(figures),
                    settings.DOCLING_ENABLED,
                )
        except Exception as exc:
            logger.warning(
                "Figuras falharam para %s (%s); seguindo sem figuras.",
                document_id,
                exc,
            )

        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_PROCESSING,
            status_detail="Generating legal analysis",
            error_message=None,
        )

        analyzer = LegalAnalyzer()
        v2_artifact_content: dict | None = None
        try:
            doc = get_document(db, id=document_id)
            strategy_prompt = (
                get_default_strategy_prompt(db, user_id=doc.user_id)
                if doc is not None
                else None
            )
            ai_data = analyzer.analyze_petition(
                analysis_text, strategy_prompt=strategy_prompt
            )

            if ai_data.get("kind") == "extraction_diagnostic":
                raise AnalysisError(
                    "Analise indisponivel: somente diagnostico de extracao.",
                    code="PROVIDER_UNAVAILABLE",
                    retryable=True,
                )

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
            # V2 T11: artefato honesto (ponte legada) para o dossiê.
            try:
                legacy_artifact = coerce_legacy_analysis(ai_data)
                v2_artifact_content = legacy_artifact.model_dump()
            except Exception as exc:
                logger.warning("Coerção legada V2 falhou (%s); sem artefato.", exc)
        except AnalysisError as ai_exc:
            # V2 T01: falha de IA nunca vira COMPLETED nem tese genérica.
            code = getattr(ai_exc, "code", "ANALYSIS_FAILED") or "ANALYSIS_FAILED"
            logger.error("Analise falhou para %s [%s]: %s", document_id, code, ai_exc)
            db.rollback()
            if run is not None:
                try:
                    transition_run(
                        db, run=run, status=AnalysisRun.FAILED,
                        stage=AnalysisRun.STAGE_COMPOSITION,
                        error_code=code, error_message=str(ai_exc),
                    )
                except Exception:
                    pass
            update_document_state(
                db,
                id=document_id,
                status=Document.STATUS_ERROR,
                status_detail="AI provider unavailable; analysis not completed",
                error_message=f"{code}: Provedor de IA indisponivel. Verifique a configuracao e reenvie.",
            )
            audit_document_completion(db, document=get_document(db, id=document_id))
            return
        except Exception as ai_exc:
            logger.error("OpenAI falhou: %s.", ai_exc)
            db.rollback()
            if run is not None:
                try:
                    transition_run(
                        db, run=run, status=AnalysisRun.FAILED,
                        stage=AnalysisRun.STAGE_COMPOSITION,
                        error_code="PROVIDER_UNAVAILABLE", error_message=str(ai_exc),
                    )
                except Exception:
                    pass
            update_document_state(
                db,
                id=document_id,
                status=Document.STATUS_ERROR,
                status_detail="AI provider unavailable; analysis not completed",
                error_message=f"PROVIDER_UNAVAILABLE: Provedor de IA indisponivel. Verifique a configuracao e reenvie.",
            )
            audit_document_completion(db, document=get_document(db, id=document_id))
            return

        db.commit()
        update_document_state(
            db,
            id=document_id,
            status=Document.STATUS_COMPLETED,
            status_detail="Analysis ready",
            error_message=None,
            completed_at=datetime.now(timezone.utc),
        )
        audit_document_completion(db, document=get_document(db, id=document_id))

        # V2 T11: publica o artefato com o status do verificador (T10).
        if run is not None and v2_artifact_content is not None:
            try:
                report = verify(coerce_legacy_analysis(ai_data if isinstance(ai_data, dict) else {}))
                publish_artifact(
                    db, run=run, content=v2_artifact_content,
                    status=decide_status(report),
                    quality_notes={
                        "errors": report.errors, "warnings": report.warnings,
                        "pending_actions": report.pending_actions,
                    },
                )
            except VersionConflictError:
                logger.info("Run %s já publicado; mantendo artefato atual.", run.id)
            except Exception as exc:
                logger.warning("Publicação V2 falhou para %s (%s).", document_id, exc)

        try:
            index_document_chunks(document_id, analysis_text)
        except Exception as exc:
            # Vector indexing must never fail the whole task.
            logger.warning(
                "Indexacao vetorial falhou para %s (%s); seguindo.", document_id, exc
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
        audit_document_completion(db, document=get_document(db, id=document_id))
        raise
    finally:
        db.close()

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.schemas.document import DocumentCreate


def delete_document_cascade(db: Session, *, document: Document) -> dict:
    """Exclusão rastreável total (V2 T13, §16).

    Remove texto, vetores, figuras, revisões/blocos, runs/artefatos/
    fontes/eventos, gerações e análise. Retorna contagens p/ auditoria.
    Arquivos em disco são removidos pelo chamador (rota).
    """
    from app.models.analysis import Analysis
    from app.models.analysis_artifact import AnalysisArtifact
    from app.models.analysis_run import AnalysisRun
    from app.models.document_chunk import DocumentChunk
    from app.models.document_figure import DocumentFigure
    from app.models.document_revision import DocumentRevision
    from app.models.generated_document import GeneratedDocument
    from app.models.review_event import ReviewEvent
    from app.models.source_block import SourceBlock
    from app.models.source_reference import SourceReference

    counts: dict[str, int] = {}

    def _drop(query, label: str) -> None:
        counts[label] = query.delete(synchronize_session=False)

    analysis_ids = [
        row.id for row in db.query(Analysis.id).filter(
            Analysis.document_id == document.id
        ).all()
    ]
    if analysis_ids:
        _drop(
            db.query(GeneratedDocument).filter(
                GeneratedDocument.analysis_id.in_(analysis_ids)
            ),
            "generated_documents",
        )
    _drop(
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id),
        "chunks",
    )
    _drop(
        db.query(DocumentFigure).filter(DocumentFigure.document_id == document.id),
        "figures",
    )
    revision_ids = [
        row.id for row in db.query(DocumentRevision.id).filter(
            DocumentRevision.document_id == document.id
        ).all()
    ]
    if revision_ids:
        _drop(
            db.query(SourceBlock).filter(SourceBlock.revision_id.in_(revision_ids)),
            "source_blocks",
        )
        _drop(
            db.query(DocumentRevision).filter(DocumentRevision.id.in_(revision_ids)),
            "revisions",
        )
    run_ids = [
        row.id for row in db.query(AnalysisRun.id).filter(
            AnalysisRun.document_id == document.id
        ).all()
    ]
    if run_ids:
        artifact_ids = [
            row.id for row in db.query(AnalysisArtifact.id).filter(
                AnalysisArtifact.run_id.in_(run_ids)
            ).all()
        ]
        if artifact_ids:
            _drop(
                db.query(ReviewEvent).filter(ReviewEvent.artifact_id.in_(artifact_ids)),
                "review_events",
            )
        _drop(
            db.query(SourceReference).filter(SourceReference.run_id.in_(run_ids)),
            "source_references",
        )
        _drop(
            db.query(AnalysisArtifact).filter(AnalysisArtifact.run_id.in_(run_ids)),
            "artifacts",
        )
        _drop(
            db.query(AnalysisRun).filter(AnalysisRun.id.in_(run_ids)),
            "runs",
        )
    if analysis_ids:
        _drop(
            db.query(Analysis).filter(Analysis.id.in_(analysis_ids)),
            "analyses",
        )
    db.delete(document)
    db.commit()
    counts["documents"] = 1
    return counts

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

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document_figure import DocumentFigure


def replace_document_figures(
    db: Session,
    *,
    document_id: UUID | str,
    user_id: UUID | str,
    figures: list[dict],
) -> list[DocumentFigure]:
    """Idempotent: substitui todas as figuras do documento."""
    db.query(DocumentFigure).filter(
        DocumentFigure.document_id == document_id
    ).delete()
    rows: list[DocumentFigure] = []
    for item in figures or []:
        rows.append(
            DocumentFigure(
                document_id=document_id,
                user_id=user_id,
                page_number=item.get("page_number"),
                bbox=item.get("bbox"),
                caption=item.get("caption"),
                file_path=item.get("file_path"),
                content_type=item.get("content_type") or "image/png",
            )
        )
    if rows:
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
    else:
        db.commit()
    return rows


def list_document_figures(
    db: Session,
    *,
    document_id: UUID | str,
    user_id: UUID | str,
) -> list[DocumentFigure]:
    return (
        db.query(DocumentFigure)
        .filter(
            DocumentFigure.document_id == document_id,
            DocumentFigure.user_id == user_id,
        )
        .order_by(DocumentFigure.page_number, DocumentFigure.created_at)
        .all()
    )


def get_document_figure(
    db: Session,
    *,
    figure_id: UUID | str,
    user_id: UUID | str,
) -> DocumentFigure | None:
    return (
        db.query(DocumentFigure)
        .filter(
            DocumentFigure.id == figure_id,
            DocumentFigure.user_id == user_id,
        )
        .first()
    )

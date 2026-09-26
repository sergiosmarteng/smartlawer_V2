"""Persistência do inventário de extração (V2 T03, §6/§8.1).

Revisão por hash do arquivo (reenvio reutiliza); blocos substituídos
de forma idempotente. Falhas de inventário nunca derrubam o pipeline —
o chamador trata como pendência explícita.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document_revision import DocumentRevision
from app.models.source_block import SourceBlock


def get_or_create_revision(
    db: Session,
    *,
    document_id: UUID | str,
    user_id: UUID | str,
    file_sha256: str,
    pages_total: int | None = None,
    origin: str | None = None,
) -> tuple[DocumentRevision, bool]:
    """Retorna (revisão, criada_agora). Mesmo hash reutiliza a revisão."""
    existing = (
        db.query(DocumentRevision)
        .filter(
            DocumentRevision.document_id == document_id,
            DocumentRevision.sha256 == file_sha256,
        )
        .order_by(DocumentRevision.created_at)
        .first()
    )
    if existing is not None:
        return existing, False
    revision = DocumentRevision(
        document_id=document_id,
        user_id=user_id,
        sha256=file_sha256,
        pages_total=pages_total,
        origin=origin,
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return revision, True


def replace_source_blocks(
    db: Session,
    *,
    revision: DocumentRevision,
    pages: list[dict],
) -> int:
    """Idempotente: substitui todos os blocos da revisão. Retorna total."""
    db.query(SourceBlock).filter(
        SourceBlock.revision_id == revision.id
    ).delete()
    rows: list[SourceBlock] = []
    for page in pages:
        for block in page.get("blocks", []):
            rows.append(
                SourceBlock(
                    revision_id=revision.id,
                    user_id=revision.user_id,
                    block_uid=block.get("id", ""),
                    page_number=page.get("page_number", 0),
                    block_type=block.get("type", "text"),
                    reading_order=block.get("reading_order", 0),
                    bbox=block.get("bbox"),
                    original_text=block.get("original_text"),
                    normalized_text=block.get("normalized_text"),
                    text_hash=SourceBlock.hash_text(block.get("original_text")),
                    extraction_method=page.get("method"),
                    quality_flags=block.get("quality_flags", []),
                )
            )
    if rows:
        db.add_all(rows)
    db.commit()
    return len(rows)


def list_blocks_for_revision(
    db: Session,
    *,
    revision_id: UUID | str,
    user_id: UUID | str,
    page_number: int | None = None,
) -> list[SourceBlock]:
    query = db.query(SourceBlock).filter(
        SourceBlock.revision_id == revision_id,
        SourceBlock.user_id == user_id,
    )
    if page_number is not None:
        query = query.filter(SourceBlock.page_number == page_number)
    return query.order_by(
        SourceBlock.page_number, SourceBlock.reading_order
    ).all()


def latest_revision_for_document(
    db: Session, *, document_id: UUID | str, user_id: UUID | str
) -> DocumentRevision | None:
    return (
        db.query(DocumentRevision)
        .filter(
            DocumentRevision.document_id == document_id,
            DocumentRevision.user_id == user_id,
        )
        .order_by(DocumentRevision.created_at.desc())
        .first()
    )

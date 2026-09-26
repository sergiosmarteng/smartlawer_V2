import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SourceBlock(Base):
    """Bloco de texto/imagem com proveniência exata (V2 §6/§8.1).

    ID estável na revisão; bbox normalizada 0-1; texto original
    preservado + normalizado; citações conferem contra o original.
    """

    __tablename__ = "source_blocks"
    __table_args__ = (
        Index("ix_source_blocks_revision", "revision_id"),
        Index("ix_source_blocks_page", "revision_id", "page_number"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    block_uid = Column(String(32), nullable=False)
    page_number = Column(Integer, nullable=False)
    page_label = Column(String(64), nullable=True)
    block_type = Column(String(30), nullable=False, default="text")
    reading_order = Column(Integer, nullable=False, default=0)
    bbox = Column(JSONB, nullable=True)
    original_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    text_hash = Column(String(64), nullable=True)
    extraction_method = Column(String(40), nullable=True)
    quality_flags = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    revision = relationship("DocumentRevision", back_populates="blocks")
    user = relationship("User")

    @staticmethod
    def hash_text(text: str | None) -> str | None:
        if not text:
            return None
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

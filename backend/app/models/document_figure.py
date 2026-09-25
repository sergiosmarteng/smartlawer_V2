import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentFigure(Base):
    """Figura extraída de um documento (Docling/fitz fallback).

    Uma linha por imagem encontrada na petição: página, bbox, legenda
    e o crop salvo em disco. Tenant via ``user_id`` (sempre filtrar).
    """

    __tablename__ = "document_figures"
    __table_args__ = (
        Index("ix_document_figures_document", "document_id"),
        Index("ix_document_figures_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    page_number = Column(Integer, nullable=True)
    bbox = Column(JSONB, nullable=True)
    caption = Column(Text, nullable=True)
    file_path = Column(String(1024), nullable=True)
    content_type = Column(String(100), nullable=False, default="image/png")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    document = relationship("Document", back_populates="figures")
    user = relationship("User")

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentRevision(Base):
    """Revisão imutável de um documento (V2 §8.1).

    ``sha256`` do arquivo identifica a revisão; reenvio do mesmo
    conteúdo reutiliza a revisão existente. Original nunca reescrito.
    """

    __tablename__ = "document_revisions"
    __table_args__ = (
        Index("ix_document_revisions_document", "document_id"),
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
    sha256 = Column(String(64), nullable=False)
    pages_total = Column(Integer, nullable=True)
    origin = Column(String(255), nullable=True)
    extra = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    document = relationship("Document")
    user = relationship("User")
    blocks = relationship(
        "SourceBlock",
        back_populates="revision",
        cascade="all, delete-orphan",
    )

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

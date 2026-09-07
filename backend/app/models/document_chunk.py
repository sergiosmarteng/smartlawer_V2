import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.core.database import Base


class DocumentChunk(Base):
    """Vector chunk of a legal document for RAG retrieval.

    Tenant isolation is enforced via ``user_id``: every retrieval query
    MUST filter by ``user_id`` (and ``document_id``/``matter_id`` when
    scoped) before running ANN search. ``embedding_model_version`` is
    stored to allow safe re-indexing when the embedding model changes.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_document", "document_id"),
        Index("ix_document_chunks_user", "user_id"),
        Index("ix_document_chunks_matter", "matter_id"),
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
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
    matter_id = Column(UUID(as_uuid=True), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=False)
    embedding_model = Column(
        String(100), nullable=False, default=settings.EMBEDDING_MODEL
    )
    embedding_model_version = Column(
        String(50), nullable=False, default=settings.EMBEDDING_MODEL_VERSION
    )
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    document = relationship("Document", back_populates="chunks")
    user = relationship("User")

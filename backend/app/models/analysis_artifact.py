import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisArtifact(Base):
    """Resultado versionado de uma execução (V2 §8.1).

    Conteúdo validado em JSONB com ``schema_version``; um ponteiro
    explícito em ``AnalysisRun.published_artifact_id`` identifica a
    revisão publicada. Revisão humana independente (§7).
    """

    __tablename__ = "analysis_artifacts"
    __table_args__ = (
        Index("ix_analysis_artifacts_run", "run_id"),
    )

    # Estado de revisão humana (§7) — independente do status da execução.
    REVIEW_PENDING = "pending"
    REVIEW_IN_REVIEW = "in_review"
    REVIEW_APPROVED = "approved"
    REVIEW_REJECTED = "rejected"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    schema_version = Column(String(20), nullable=False, default="2.0")
    status = Column(String(30), nullable=False, default="partial")
    review_status = Column(String(30), nullable=False, default=REVIEW_PENDING)
    content = Column(JSONB, nullable=True)
    content_hash = Column(String(128), nullable=True)
    quality_notes = Column(JSONB, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    run = relationship(
        "AnalysisRun", back_populates="artifact", foreign_keys=[run_id]
    )
    user = relationship("User")

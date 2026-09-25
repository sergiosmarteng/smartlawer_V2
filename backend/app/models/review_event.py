import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReviewEvent(Base):
    """Correção ou decisão humana sobre um artefato (V2 §8.1/§12.1).

    Preserva saída original e autoria: antes/depois, justificativa e
    versão de origem. Aprovação liga-se à versão e ao escopo revisado.
    """

    __tablename__ = "review_events"
    __table_args__ = (
        Index("ix_review_events_artifact", "artifact_id"),
        Index("ix_review_events_user", "reviewer_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_artifacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    target = Column(String(255), nullable=False, default="artifact")
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    source_version = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    artifact = relationship("AnalysisArtifact")
    reviewer = relationship("User")

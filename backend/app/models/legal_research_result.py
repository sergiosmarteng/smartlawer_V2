"""Fonte externa consultada e verificada (Onda 0 Task 9, §8.9 + §14)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LegalResearchResult(Base):
    __tablename__ = "legal_research_results"
    __table_args__ = (
        Index("ix_legal_research_results_run", "run_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    issue_id = Column(String(120), nullable=True)
    url = Column(Text, nullable=True)
    organ = Column(String(120), nullable=True)
    identifier = Column(String(255), nullable=True)
    excerpt = Column(Text, nullable=True)
    consulted_at = Column(String(20), nullable=True)
    status = Column(String(30), nullable=False, default="partial")
    extra = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    run_row = relationship("AnalysisRun")
    user = relationship("User")

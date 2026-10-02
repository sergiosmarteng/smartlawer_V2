"""Cálculo determinístico persistido (Onda 0 Task 9, §8.10)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CalculationResult(Base):
    __tablename__ = "calculation_results"
    __table_args__ = (
        Index("ix_calculation_results_run", "run_id"),
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
    formula = Column(String(120), nullable=False)
    formula_version = Column(String(20), nullable=False, default="1.0")
    inputs = Column(JSONB, nullable=True)
    result = Column(String(64), nullable=True)
    output_hash = Column(String(128), nullable=True)
    reproducible = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    run_row = relationship("AnalysisRun")
    user = relationship("User")

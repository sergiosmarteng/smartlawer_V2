"""Checkpoint de estágio do pipeline V3 (Onda 0 Task 2, §8.2).

Cada chamada ``start_stage`` registra um ``AnalysisStageRun`` com
``(run_id, stage, attempt)`` único. ``finish_stage`` e ``fail_stage``
marcam o desfecho e métricas. ``get_resume_point`` lê a sequência ordenada
de estágios para retomar o pipeline V3 do ponto em que parou.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisStageRun(Base):
    __tablename__ = "analysis_stage_runs"
    __table_args__ = (
        Index("ix_analysis_stage_runs_run", "run_id"),
        UniqueConstraint("run_id", "stage", "attempt", name="uq_stage_run_stage_attempt"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage = Column(String(60), nullable=False)
    attempt = Column(Integer, nullable=False, default=1)

    # Estados do estágio.
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    status = Column(String(30), nullable=False, default=STATUS_RUNNING)
    started_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    metrics = Column(JSONB, nullable=True)
    error_code = Column(String(60), nullable=True)
    error_message = Column(Text, nullable=True)
    retryable = Column(Integer, nullable=True)  # 1 se o verificador marcou como retentável.

    run_row = relationship("AnalysisRun")
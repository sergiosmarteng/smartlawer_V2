import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisRun(Base):
    """Uma execução versionada da análise (V2 §7/§8.1).

    Identidade imutável ligada ao snapshot dos documentos e à
    configuração. Reanalisar cria nova execução — nunca sobrescreve.
    A tabela legada ``analyses`` permanece como projeção compatível.
    """

    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_user", "user_id"),
        Index("ix_analysis_runs_document", "document_id"),
        Index("ix_analysis_runs_status", "status"),
    )

    # Estados de execução (§7).
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_RETRY = "waiting_retry"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"

    TERMINAL_STATUSES = frozenset({COMPLETED, PARTIAL, FAILED, CANCELLED})

    # Etapas do pipeline (§7).
    STAGE_EXTRACTION = "extraction"
    STAGE_CLASSIFICATION = "classification"
    STAGE_STRUCTURED_EXTRACTION = "structured_extraction"
    STAGE_RECONCILIATION = "reconciliation"
    STAGE_RESEARCH = "research"
    STAGE_CALCULATIONS = "calculations"
    STAGE_VERIFICATION = "verification"
    STAGE_COMPOSITION = "composition"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    status = Column(String(30), nullable=False, default=QUEUED)
    stage = Column(String(40), nullable=True)
    # Snapshot: revisões de documentos, config, modelo/provedor por etapa,
    # versões de prompt/regras, orçamento.
    snapshot = Column(JSONB, nullable=True)
    idempotency_key = Column(String(255), nullable=True)
    error_code = Column(String(60), nullable=True)
    error_message = Column(Text, nullable=True)
    published_artifact_id = Column(
        UUID(as_uuid=True),
        # Ponteiro explícito sem FK (evita ciclo runs↔artifacts);
        # integridade garantida pelo CRUD em transação curta (§7.2).
        nullable=True,
    )
    # Lock otimista para publicação concorrente (§7.2).
    version = Column(Integer, nullable=False, default=1)
    usage = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    document = relationship("Document")
    artifact = relationship(
        "AnalysisArtifact",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="AnalysisArtifact.run_id",
    )

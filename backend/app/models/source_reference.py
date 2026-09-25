import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SourceReference(Base):
    """Fonte documental ou jurídica externa de uma execução (V2 §8.1).

    Toda afirmação factual material do artefato deve resolver para uma
    referência autorizada (§8.4). ``verification_status`` distingue o
    trecho conferido do não verificado — nunca inventar URL ou teor.
    """

    __tablename__ = "source_references"
    __table_args__ = (
        Index("ix_source_references_run", "run_id"),
        Index("ix_source_references_user", "user_id"),
    )

    KIND_DOCUMENT = "document"
    KIND_EXTERNAL = "external"
    KIND_DERIVED = "derived"

    VERIFICATION_MATCHED = "matched"
    VERIFICATION_UNVERIFIED = "unverified"
    VERIFICATION_INSUFFICIENT = "insufficient"
    VERIFICATION_CONTRADICTORY = "contradictory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    kind = Column(String(30), nullable=False, default=KIND_DOCUMENT)
    revision_id = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    block_id = Column(String(255), nullable=True)
    quote = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    verification_status = Column(
        String(30), nullable=False, default=VERIFICATION_UNVERIFIED
    )
    content_hash = Column(String(128), nullable=True)
    extra = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    run = relationship("AnalysisRun")
    user = relationship("User")

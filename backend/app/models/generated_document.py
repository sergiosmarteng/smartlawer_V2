import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class GeneratedDocument(Base):
    """Persisted DOCX generation history (C2/BL-017).

    Every successful ``generate`` records one versioned row pointing at a
    managed file under the uploads volume, so any previous version can be
    recovered. Retention (see ``GENERATED_KEEP_LATEST``) trims old versions.
    """

    __tablename__ = "generated_documents"
    __table_args__ = (
        UniqueConstraint("analysis_id", "version", name="uq_generated_analysis_version"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    file_path = Column(String(1024), nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    analysis = relationship("Analysis")

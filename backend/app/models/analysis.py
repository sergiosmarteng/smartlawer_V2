import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    requests = Column(JSONB, nullable=True) # List of requests
    laws = Column(JSONB, nullable=True) # List of laws cited
    evidence = Column(JSONB, nullable=True)
    defense_theses = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    document = relationship("Document", back_populates="analysis")

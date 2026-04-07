import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    content_type = Column(String(100), default="application/pdf")
    status = Column(String(50), default="uploaded") # uploaded, processing, completed, error
    uploaded_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    user = relationship("User")
    analysis = relationship("Analysis", back_populates="document", uselist=False)

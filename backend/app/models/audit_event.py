import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from app.core.database import Base


class AuditEvent(Base):
    """Queryable audit trail (C4/BL-018 + BL-024).

    Low-volume security/workflow events only (auth, uploads, generations,
    template/prompt management, chat usage, pipeline completion/failure).
    Raw user content (queries, documents) is NEVER stored — only ids,
    counts, timings and result states.
    """

    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(64), nullable=True)
    meta = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # event_type vocabulary (keep in sync with app/core/audit.py)
    AUTH_REGISTER = "auth.register"
    AUTH_LOGIN = "auth.login"
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_COMPLETED = "document.completed"
    DOCUMENT_FAILED = "document.failed"
    DOCX_GENERATED = "docx.generated"
    TEMPLATE_UPLOAD = "template.upload"
    PROMPT_CREATED = "prompt.created"
    PROMPT_DEFAULT = "prompt.default"
    PROMPT_DELETED = "prompt.deleted"
    CHAT_QUERY = "chat.query"

import uuid
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.core.database import Base


class PromptProfile(Base):
    """User-owned AI run customization (C3/BL-020).

    ``strategy_prompt`` is extra guidance prepended to the analyzer prompt
    for documents processed while the profile is default. Only one default
    per user (enforced at the route layer, newest wins on conflict).
    """

    __tablename__ = "prompt_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    strategy_prompt = Column(Text, nullable=False, default="")
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

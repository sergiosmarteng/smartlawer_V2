from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field


class AuditEventBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditEventResponse(AuditEventBase):
    id: UUID4
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    meta: dict = Field(default_factory=dict)
    created_at: datetime | None = None


class OpsSummaryResponse(BaseModel):
    documents_by_status: dict[str, int] = Field(default_factory=dict)
    events_24h: dict[str, int] = Field(default_factory=dict)
    recent_failures: list[AuditEventResponse] = Field(default_factory=list)

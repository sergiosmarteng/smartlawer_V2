from datetime import datetime

from pydantic import UUID4, Field

from app.schemas.workflow import WorkflowBase


class TemplateResponse(WorkflowBase):
    id: UUID4
    name: str
    placeholders: list[str] = Field(default_factory=list)
    unsupported_placeholders: list[str] = Field(
        default_factory=list, alias="unsupportedPlaceholders"
    )
    created_at: datetime | None = None

from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field


class PromptProfileBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PromptProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    strategy_prompt: str = Field(default="", max_length=2000)
    is_default: bool = False


class PromptProfileResponse(PromptProfileBase):
    id: UUID4
    name: str
    strategy_prompt: str = ""
    is_default: bool = False
    created_at: datetime | None = None

"""Schemas da API V2 do dossiê (T11, §14)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowV2Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorEnvelope(WorkflowV2Base):
    code: str
    stage: str | None = None
    retryable: bool = False
    user_message: str
    correlation_id: str


class CreateRunRequest(WorkflowV2Base):
    document_ids: list[UUID] = Field(min_length=1)
    case_id: UUID | None = None
    represented_side: str = "neutral"
    objective: str | None = None
    reference_date: str | None = None
    area_overrides: list[str] = Field(default_factory=list)
    module_id: str = "general"
    idempotency_key: str | None = None


class CreateRunResponse(WorkflowV2Base):
    run_id: UUID
    status_url: str
    status: str


class RunStatusResponse(WorkflowV2Base):
    run_id: UUID
    status: str
    stage: str | None = None
    progress: int
    version: int = 1
    stages: list[dict] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    artifact_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class ArtifactResponse(WorkflowV2Base):
    id: UUID
    run_id: UUID
    schema_version: str
    status: str
    review_status: str
    content: dict = Field(default_factory=dict)
    content_hash: str | None = None
    quality_notes: Any = None
    published_at: datetime | None = None
    legacy: bool = False
    reanalyze_available: bool = False


class CaseCreateRequest(WorkflowV2Base):
    name: str | None = None
    area: str | None = None
    description: str | None = None


class CaseResponse(WorkflowV2Base):
    id: UUID
    name: str | None = None
    area: str | None = None
    documents: list[dict] = Field(default_factory=list)
    created_at: datetime | None = None


class AttachDocumentRequest(WorkflowV2Base):
    document_id: UUID
    role: str = "documento"


class VisualResponse(WorkflowV2Base):
    id: str
    page_number: int | None = None
    kind: str | None = None
    storage_key: str | None = None
    thumbnail_key: str | None = None


class VersionResponse(WorkflowV2Base):
    id: UUID
    run_id: UUID
    schema_version: str
    status: str
    created_at: datetime | None = None


class CompareResponse(WorkflowV2Base):
    before_id: UUID
    after_id: UUID
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)


class SectionResponse(WorkflowV2Base):
    section: str
    total: int
    page: int
    page_size: int
    items: list[Any] = Field(default_factory=list)


class SourceResponse(WorkflowV2Base):
    id: UUID
    kind: str
    revision_id: str | None = None
    page_number: int | None = None
    block_id: str | None = None
    quote: str | None = None
    url: str | None = None
    verification_status: str
    document_id: UUID | None = None


class ReviewEventRequest(WorkflowV2Base):
    target: str = "artifact"
    before: Any = None
    after: Any = None
    reason: str | None = None
    expected_version: int | None = None


class ReviewEventResponse(WorkflowV2Base):
    id: UUID
    target: str
    reason: str | None = None
    source_version: str | None = None
    created_at: datetime | None = None


class ExportRequest(WorkflowV2Base):
    mode: str = "complete"


class ExportResponse(WorkflowV2Base):
    job_id: str
    download_url: str
    mode: str

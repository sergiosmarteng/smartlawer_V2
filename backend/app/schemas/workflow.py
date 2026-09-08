from datetime import datetime
from typing import Any

from pydantic import UUID4, BaseModel, ConfigDict, Field


class WorkflowBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProcessResponse(WorkflowBase):
    id: UUID4
    analysis_id: UUID4 | None = None
    title: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    status_detail: str | None = None
    analysis_url: str | None = None
    docx_download_url: str | None = Field(default=None, alias="docxDownloadUrl")


class UploadSubmissionResponse(WorkflowBase):
    id: UUID4
    task_id: UUID4
    user_id: UUID4
    filename: str
    content_type: str
    status: str
    status_detail: str | None = None
    uploaded_at: datetime | None = None
    task_status_url: str = Field(alias="taskStatusUrl")
    analysis_id: UUID4 | None = None
    analysis_url: str | None = None
    docx_download_url: str | None = Field(default=None, alias="docxDownloadUrl")


class TaskStatusResponse(WorkflowBase):
    task_id: UUID4
    document_id: UUID4
    title: str
    status: str
    progress: int
    analysis_id: UUID4 | None = None
    status_detail: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    analysis_url: str | None = None
    docx_download_url: str | None = Field(default=None, alias="docxDownloadUrl")


class AnalysisDetailResponse(WorkflowBase):

    id: UUID4
    document_id: UUID4
    document_name: str = Field(alias="documentName")
    title: str
    summary: str
    key_arguments: list[str] = Field(default_factory=list, alias="keyArguments")
    requests: list[str] = Field(default_factory=list)
    laws: list[str] = Field(default_factory=list)
    evidence: Any = None
    defense_theses: list[str] = Field(default_factory=list)
    status: str | None = None
    status_detail: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    generated_defense_strategy: str = Field(alias="generatedDefenseStrategy")
    docx_download_url: str | None = Field(default=None, alias="docxDownloadUrl")


class GeneratedVersionResponse(WorkflowBase):
    """One persisted DOCX generation (C2/BL-017 history)."""

    version: int
    template_id: UUID4 | None = None
    created_at: datetime | None = None
    download_url: str | None = Field(default=None, alias="downloadUrl")


class BatchUploadError(WorkflowBase):
    filename: str
    detail: str


class BatchUploadResponse(WorkflowBase):
    """Result of a multi-PDF batch upload (C3/BL-021)."""

    items: list[UploadSubmissionResponse] = Field(default_factory=list)
    errors: list[BatchUploadError] = Field(default_factory=list)

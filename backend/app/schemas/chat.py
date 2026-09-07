from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    document_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    ref: str
    chunk_id: str
    document_id: str
    document_name: str
    page_start: int | None = None
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model: str
    ai_draft: bool = True
    requires_human_review: bool = True

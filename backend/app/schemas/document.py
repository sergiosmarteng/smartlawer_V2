from typing import Optional
from pydantic import BaseModel, UUID4
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    content_type: str

class DocumentCreate(DocumentBase):
    user_id: UUID4
    file_path: str

class DocumentResponse(DocumentBase):
    id: UUID4
    user_id: UUID4
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

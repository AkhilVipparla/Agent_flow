from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunk_count: int
    created_at: datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    created_at: datetime

from __future__ import annotations

from datetime import datetime

from app.schemas.common import CamelModel


class DocumentUploadResponse(CamelModel):
    id: str
    filename: str
    status: str
    chunk_count: int
    created_at: datetime


class DocumentResponse(CamelModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    created_at: datetime
    # True when the original file is stored and can be previewed (PDFs uploaded since previews existed).
    has_file: bool = False

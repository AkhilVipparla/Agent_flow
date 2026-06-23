from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from app.schemas.documents import DocumentUploadResponse
from app.services.embedding_service import EmbeddingProtocol
from app.services.qdrant_service import VectorSearchProtocol
from app.tools.excel_parser_tool import parse_excel
from app.tools.pdf_parser_tool import parse_pdf

_ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}


async def ingest_document(
    filename: str,
    tmp_path: str,
    embedder: EmbeddingProtocol,
    vector_db: VectorSearchProtocol,
) -> DocumentUploadResponse:
    _, ext = os.path.splitext(filename.lower())
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    chunks = await _extract_chunks(tmp_path, ext)
    doc_id = str(uuid.uuid4())
    for i, text in enumerate(chunks):
        vector = embedder.embed_text(text)
        await vector_db.upsert(
            id=f"{doc_id}-chunk-{i}",
            vector=vector,
            content=text,
            metadata={"doc_id": doc_id, "filename": filename, "chunk": i},
        )
    return DocumentUploadResponse(
        id=doc_id,
        filename=filename,
        status="ingested",
        chunk_count=len(chunks),
        created_at=datetime.now(timezone.utc),
    )


async def _extract_chunks(path: str, ext: str) -> list[str]:
    if ext == ".pdf":
        pages = await parse_pdf(path)
        return [p["text"] for p in pages if p.get("text")]
    sheets = await parse_excel(path)
    chunks: list[str] = []
    for sheet in sheets:
        header_line = ", ".join(sheet["headers"])
        for row in sheet["rows"]:
            chunks.append(f"{header_line}: {', '.join(str(v) for v in row.values())}")
    return chunks or ["(empty document)"]

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

from app.schemas.documents import DocumentResponse, DocumentUploadResponse
from app.services.embedding_service import EmbeddingProtocol
from app.services.postgres_service import DatabaseProtocol
from app.services.qdrant_service import VectorSearchProtocol
from app.services.request_context import current_owner
from app.tools.excel_parser_tool import parse_excel
from app.tools.pdf_parser_tool import parse_pdf

_ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}

_EXT_TO_FILE_TYPE = {".pdf": "pdf", ".csv": "csv", ".xlsx": "excel", ".xls": "excel"}


async def ingest_document(
    filename: str,
    tmp_path: str,
    embedder: EmbeddingProtocol,
    vector_db: VectorSearchProtocol,
    db: DatabaseProtocol,
) -> DocumentUploadResponse:
    _, ext = os.path.splitext(filename.lower())
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    chunks = await _extract_chunks(tmp_path, ext)
    if not chunks:
        raise ValueError(
            "No text could be extracted from this file. Scanned or image-only PDFs are not supported."
        )
    doc_id = str(uuid.uuid4())
    owner = current_owner()
    vectors = await asyncio.to_thread(embedder.embed_batch, chunks)
    for i, (text, vector) in enumerate(zip(chunks, vectors)):
        await vector_db.upsert(
            id=f"{doc_id}-chunk-{i}",
            vector=vector,
            content=text,
            metadata={
                "doc_id": doc_id, "filename": filename, "chunk": i, "source": filename,
                "page": i + 1, "owner_id": owner,
            },
        )
    created_at = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO documents (id, filename, file_type, chunk_count, created_at, owner_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        (doc_id, filename, _EXT_TO_FILE_TYPE[ext], len(chunks), created_at, owner),
    )
    return DocumentUploadResponse(
        id=doc_id,
        filename=filename,
        status="ingested",
        chunk_count=len(chunks),
        created_at=created_at,
    )


async def list_documents(db: DatabaseProtocol) -> list[DocumentResponse]:
    rows = await db.fetch_many(
        "SELECT * FROM documents WHERE owner_id = $1 ORDER BY created_at DESC", (current_owner(),)
    )
    return [
        DocumentResponse(
            id=row.get("id", ""),
            filename=row.get("filename", ""),
            file_type=row.get("file_type", ""),
            chunk_count=row.get("chunk_count", 0),
            created_at=row.get("created_at") or datetime.now(timezone.utc),
        )
        for row in rows
    ]


async def delete_document(
    doc_id: str,
    vector_db: VectorSearchProtocol,
    db: DatabaseProtocol,
) -> bool:
    """Remove a document's chunks from the vector store and its metadata row.

    Returns False if the document does not exist.
    """
    owner = current_owner()
    row = await db.fetch_one("SELECT * FROM documents WHERE id = $1 AND owner_id = $2", (doc_id, owner))
    if row is None:
        return False
    for i in range(row.get("chunk_count", 0)):
        await vector_db.delete(f"{doc_id}-chunk-{i}")
    await db.execute("DELETE FROM documents WHERE id = $1 AND owner_id = $2", (doc_id, owner))
    return True


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

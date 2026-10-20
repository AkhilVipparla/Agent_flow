from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime

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
    for i, (text, vector) in enumerate(zip(chunks, vectors, strict=True)):
        await vector_db.upsert(
            id=f"{doc_id}-chunk-{i}",
            vector=vector,
            content=text,
            metadata={
                "doc_id": doc_id, "filename": filename, "chunk": i, "source": filename,
                "page": i + 1, "owner_id": owner,
            },
        )
    created_at = datetime.now(UTC)
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
        """
        SELECT d.*, (f.document_id IS NOT NULL) AS has_file
        FROM documents d LEFT JOIN document_files f ON f.document_id = d.id
        WHERE d.owner_id = $1
        ORDER BY d.created_at DESC
        """,
        (current_owner(),),
    )
    return [
        DocumentResponse(
            id=row.get("id", ""),
            filename=row.get("filename", ""),
            file_type=row.get("file_type", ""),
            chunk_count=row.get("chunk_count", 0),
            created_at=row.get("created_at") or datetime.now(UTC),
            has_file=bool(row.get("has_file")),
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
    # Explicit (not only ON DELETE CASCADE) so it also holds on SQLite, where foreign keys are off.
    await db.execute("DELETE FROM document_files WHERE document_id = $1", (doc_id,))
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


async def store_document_file(db: DatabaseProtocol, doc_id: str, content: bytes, content_type: str) -> None:
    """Keep the original upload so its owner can view it later."""
    await db.execute(
        "INSERT INTO document_files (document_id, content, content_type, size_bytes, created_at) "
        "VALUES ($1, $2, $3, $4, $5)",
        (doc_id, content, content_type, len(content), datetime.now(UTC)),
    )


async def get_document_file(db: DatabaseProtocol, doc_id: str) -> tuple[str, str, bytes] | None:
    """(filename, content type, bytes) for one of the current user's documents, else None."""
    row = await db.fetch_one(
        """
        SELECT d.filename, f.content_type, f.content
        FROM documents d JOIN document_files f ON f.document_id = d.id
        WHERE d.id = $1 AND d.owner_id = $2
        """,
        (doc_id, current_owner()),
    )
    if row is None:
        return None
    return row["filename"], row["content_type"], bytes(row["content"])

from __future__ import annotations

import logging
import os
import tempfile
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response, UploadFile

from app.api.dependencies import DbDep, EmbedDep, VectorDbDep
from app.config import settings
from app.schemas.documents import DocumentResponse, DocumentUploadResponse
from app.services.document_service import (
    delete_document,
    get_document_file,
    ingest_document,
    list_documents,
    store_document_file,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    embedder: EmbedDep,
    vector_db: VectorDbDep,
    db: DbDep,
) -> DocumentUploadResponse:
    filename = file.filename or "upload"
    _, ext = os.path.splitext(filename.lower())
    max_bytes = settings.max_upload_mb * 1024 * 1024
    contents = await file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File is larger than {settings.max_upload_mb} MB.")
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        uploaded = await ingest_document(filename, tmp_path, embedder, vector_db, db)
        if ext == ".pdf" and contents.startswith(b"%PDF-"):
            # Keep the original so it can be previewed. A failure here must not undo the ingest:
            # the document is still searchable, it just won't have a preview.
            try:
                await store_document_file(db, uploaded.id, contents, "application/pdf")
            except Exception:
                logger.exception("Could not store the original file for document %s", uploaded.id)
        return uploaded
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        os.unlink(tmp_path)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_all_documents(db: DbDep) -> list[DocumentResponse]:
    return await list_documents(db)


@router.delete("/documents/{doc_id}", status_code=204, response_model=None)
async def delete_document_by_id(doc_id: str, vector_db: VectorDbDep, db: DbDep) -> None:
    deleted = await delete_document(doc_id, vector_db, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/{doc_id}/file")
async def view_document_file(doc_id: str, db: DbDep) -> Response:
    """The original PDF, for the in-app viewer. Only its owner can fetch it."""
    found = await get_document_file(db, doc_id)
    if found is None:
        raise HTTPException(status_code=404, detail="No stored file for this document.")
    filename, content_type, content = found
    # Percent-encoding also neutralises CR/LF, so a hostile filename cannot inject headers.
    safe_name = quote(filename, safe="")
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{safe_name}",
            # A private user file: never let a shared cache keep it.
            "Cache-Control": "private, no-store",
            # Belt and braces for user-supplied content served from our origin.
            "Content-Security-Policy": "sandbox; default-src 'none'",
        },
    )

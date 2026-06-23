from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile

from app.api.dependencies import EmbedDep, VectorDbDep
from app.schemas.documents import DocumentResponse, DocumentUploadResponse
from app.services.document_service import ingest_document

router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    embedder: EmbedDep,
    vector_db: VectorDbDep,
) -> DocumentUploadResponse:
    filename = file.filename or "upload"
    _, ext = os.path.splitext(filename.lower())
    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return await ingest_document(filename, tmp_path, embedder, vector_db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        os.unlink(tmp_path)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents() -> list[DocumentResponse]:
    return []


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: str) -> None:
    pass

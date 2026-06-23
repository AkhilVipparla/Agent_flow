from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.services.embedding_service import EmbeddingProtocol, get_embedding_service
from app.services.postgres_service import DatabaseProtocol, get_database_service
from app.services.qdrant_service import VectorSearchProtocol, get_vector_search_service


def get_db() -> DatabaseProtocol:
    return get_database_service()


def get_vector_db() -> VectorSearchProtocol:
    return get_vector_search_service()


def get_embedder() -> EmbeddingProtocol:
    return get_embedding_service()


DbDep = Annotated[DatabaseProtocol, Depends(get_db)]
VectorDbDep = Annotated[VectorSearchProtocol, Depends(get_vector_db)]
EmbedDep = Annotated[EmbeddingProtocol, Depends(get_embedder)]

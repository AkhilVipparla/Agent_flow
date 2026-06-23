from __future__ import annotations

import logging
import os
from typing import Any

from app.services.qdrant_service import SearchResult, VectorSearchProtocol

logger = logging.getLogger(__name__)

_vector_db: VectorSearchProtocol | None = None
_embedder = None  # EmbeddingProtocol — typed loosely to avoid circular imports at module load


def _get_embedder():
    global _embedder
    if _embedder is None:
        from app.services.embedding_service import MockEmbeddingService
        _embedder = MockEmbeddingService()
    return _embedder


def _get_vector_db() -> VectorSearchProtocol:
    global _vector_db
    if _vector_db is None:
        use_mock = os.getenv("USE_MOCK_VECTOR_SEARCH", "true").lower() not in ("false", "0", "no")
        if use_mock:
            from app.services.qdrant_service import MockVectorSearch
            logger.info("VectorSearchTool: using MockVectorSearch")
            _vector_db = MockVectorSearch()
        else:
            from app.config import settings
            from app.services.qdrant_service import QdrantVectorSearch
            logger.info("VectorSearchTool: connecting to Qdrant at %s", settings.qdrant_url)
            _vector_db = QdrantVectorSearch(url=settings.qdrant_url, collection=settings.qdrant_collection)
    return _vector_db


async def vector_search(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    """Embed the query and search the vector store. Returns raw results; no reasoning.

    Raises RuntimeError if the underlying search fails.
    """
    vector = _get_embedder().embed_text(query)
    try:
        return await _get_vector_db().similarity_search(vector, top_k=top_k, filters=filters)
    except Exception as exc:
        logger.error("VectorSearchTool: similarity_search failed: %s", exc)
        raise RuntimeError("Vector search failed.") from exc

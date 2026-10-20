from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services.qdrant_service import SearchResult, VectorSearchProtocol
from app.services.request_context import current_owner

logger = logging.getLogger(__name__)

def _get_embedder():
    # Same singletons the upload path uses, so query vectors match stored ones.
    from app.services.embedding_service import get_embedding_service
    return get_embedding_service()


def _get_vector_db() -> VectorSearchProtocol:
    from app.services.qdrant_service import get_vector_search_service
    return get_vector_search_service()


async def vector_search(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    """Embed the query and search the vector store. Returns raw results; no reasoning.

    Raises RuntimeError if the underlying search fails.
    """
    vector = await asyncio.to_thread(_get_embedder().embed_text, query)
    # Always scope to the caller's own documents; a caller-supplied filter can't widen this.
    owner_filter = {"must": [{"key": "owner_id", "match": {"value": current_owner()}}]}
    filters = {**(filters or {}), "must": [*((filters or {}).get("must") or []), *owner_filter["must"]]}
    try:
        return await _get_vector_db().similarity_search(vector, top_k=top_k, filters=filters)
    except Exception as exc:
        logger.error("VectorSearchTool: similarity_search failed: %s", exc)
        raise RuntimeError("Vector search failed.") from exc

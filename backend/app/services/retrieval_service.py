from __future__ import annotations

import logging
import os
from typing import Any

from app.schemas.agents import Citation, EvidenceItem
from app.services.embedding_service import EmbeddingProtocol, MockEmbeddingService
from app.services.qdrant_service import MockVectorSearch, QdrantVectorSearch, VectorSearchProtocol

logger = logging.getLogger(__name__)


class RetrievalService:
    """Orchestrates embed → search → format for the RAG pipeline."""

    def __init__(
        self,
        vector_search: VectorSearchProtocol,
        embedder: EmbeddingProtocol,
    ) -> None:
        self._vector_search = vector_search
        self._embedder = embedder

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[EvidenceItem], list[Citation]]:
        vector = self._embedder.embed_text(query)
        results = await self._vector_search.similarity_search(vector, top_k=top_k, filters=filters)

        if not results:
            logger.warning("RetrievalService returned no results for query: %r", query)
            return [], []

        citations: list[Citation] = [
            Citation(
                source=r.metadata.get("source", r.id),
                url=r.metadata.get("url"),
                page=r.metadata.get("page"),
                excerpt=r.content[:300],
            )
            for r in results
        ]

        combined_content = "\n\n".join(
            f"[{r.metadata.get('source', r.id)}]\n{r.content}" for r in results
        )
        evidence = EvidenceItem(agent="rag", content=combined_content, citations=citations)

        return [evidence], citations


def get_retrieval_service() -> RetrievalService:
    """Factory: returns mock or real service based on USE_MOCK_VECTOR_SEARCH env var."""
    use_mock = os.getenv("USE_MOCK_VECTOR_SEARCH", "true").lower() not in ("false", "0", "no")

    if use_mock:
        logger.info("RetrievalService: using MockVectorSearch and MockEmbeddingService")
        return RetrievalService(
            vector_search=MockVectorSearch(),
            embedder=MockEmbeddingService(),
        )

    from app.config import settings
    logger.info("RetrievalService: connecting to Qdrant at %s", settings.qdrant_url)
    return RetrievalService(
        vector_search=QdrantVectorSearch(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
        ),
        embedder=MockEmbeddingService(),
    )

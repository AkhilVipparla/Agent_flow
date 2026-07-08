from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class VectorSearchProtocol(Protocol):
    async def similarity_search(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]: ...

    async def upsert(self, id: str, vector: list[float], content: str, metadata: dict[str, Any]) -> None: ...

    async def delete(self, id: str) -> None: ...

    async def ensure_collection(self) -> None: ...


# ---------------------------------------------------------------------------
# Mock — returns deterministic enterprise-looking chunks; no Qdrant required.
# ---------------------------------------------------------------------------

_MOCK_CORPUS: list[dict[str, Any]] = [
    {
        "id": "doc-001-chunk-1",
        "content": (
            "Q4 2024 Financial Results: Revenue reached $142M, a 23% year-over-year increase. "
            "Gross margin improved to 68% driven by SaaS subscription growth. "
            "Operating expenses were $89M, resulting in an operating income of $53M."
        ),
        "metadata": {
            "source": "Q4 2024 Earnings Report",
            "url": None,
            "page": 4,
            "doc_id": "doc-001",
        },
    },
    {
        "id": "doc-002-chunk-1",
        "content": (
            "2025 Product Roadmap: The platform will introduce AI-powered analytics in Q1, "
            "multi-region data residency in Q2, and an enterprise API marketplace in Q3. "
            "Headcount is projected to grow from 480 to 620 by year-end."
        ),
        "metadata": {
            "source": "2025 Strategic Roadmap",
            "url": None,
            "page": 2,
            "doc_id": "doc-002",
        },
    },
    {
        "id": "doc-003-chunk-1",
        "content": (
            "Data Governance Policy v3.1: All customer data must be encrypted at rest using AES-256 "
            "and in transit using TLS 1.3. Retention periods are 7 years for financial records and "
            "3 years for operational logs. Access is restricted to role-based permissions reviewed quarterly."
        ),
        "metadata": {
            "source": "Data Governance Policy v3.1",
            "url": None,
            "page": 8,
            "doc_id": "doc-003",
        },
    },
    {
        "id": "doc-004-chunk-1",
        "content": (
            "Customer Satisfaction Survey 2024: Net Promoter Score rose to 72 (up from 61 in 2023). "
            "Top drivers of satisfaction: reliability (94%), support responsiveness (88%), and "
            "ease of integration (82%). Churn rate decreased to 4.2% annually."
        ),
        "metadata": {
            "source": "Customer Satisfaction Survey 2024",
            "url": None,
            "page": 1,
            "doc_id": "doc-004",
        },
    },
    {
        "id": "doc-005-chunk-1",
        "content": (
            "Engineering Infrastructure Report: The platform processed 1.4 billion API calls in Q4 2024 "
            "with 99.97% uptime. P99 latency is 142ms. The migration to Kubernetes reduced infrastructure "
            "costs by 31% compared to the previous VM-based architecture."
        ),
        "metadata": {
            "source": "Engineering Infrastructure Report Q4 2024",
            "url": None,
            "page": 3,
            "doc_id": "doc-005",
        },
    },
]


class MockVectorSearch:
    """Returns the top-k mock corpus entries with descending fake scores."""

    async def similarity_search(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        results = [
            SearchResult(
                id=item["id"],
                content=item["content"],
                score=round(1.0 - idx * 0.08, 4),
                metadata=item["metadata"],
            )
            for idx, item in enumerate(_MOCK_CORPUS[:top_k])
        ]
        return results

    async def upsert(self, id: str, vector: list[float], content: str, metadata: dict[str, Any]) -> None:
        logger.info("MockVectorSearch.upsert called for id=%s (no-op)", id)

    async def delete(self, id: str) -> None:
        logger.info("MockVectorSearch.delete called for id=%s (no-op)", id)

    async def ensure_collection(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Real — wraps qdrant-client; lazy init so import never crashes.
# ---------------------------------------------------------------------------

class QdrantVectorSearch:
    """Real Qdrant implementation. Requires a running Qdrant instance."""

    def __init__(self, url: str, collection: str, api_key: str = "") -> None:
        self._url = url
        self._collection = collection
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import AsyncQdrantClient
            self._client = AsyncQdrantClient(url=self._url, api_key=self._api_key or None)
        return self._client

    # Vector size must match the embedding model (BAAI/bge-small-en-v1.5 → 384).
    _VECTOR_SIZE = 384

    async def ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams
        client = self._get_client()
        if not await client.collection_exists(self._collection):
            await client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("Qdrant collection %r created", self._collection)

    async def similarity_search(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        from qdrant_client.models import Filter
        client = self._get_client()
        hits = await client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=top_k,
            query_filter=Filter(**filters) if filters else None,
            with_payload=True,
        )
        return [
            SearchResult(
                id=str(hit.id),
                content=hit.payload.get("content", ""),
                score=hit.score,
                metadata={k: v for k, v in hit.payload.items() if k != "content"},
            )
            for hit in hits
        ]

    @staticmethod
    def _point_id(id: str) -> str:
        # Qdrant only accepts UUID or integer point IDs; app-level ids like
        # "{doc_id}-chunk-0" are mapped to a deterministic UUID.
        import uuid
        return str(uuid.uuid5(uuid.NAMESPACE_URL, id))

    async def upsert(self, id: str, vector: list[float], content: str, metadata: dict[str, Any]) -> None:
        from qdrant_client.models import PointStruct
        client = self._get_client()
        await client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=self._point_id(id),
                    vector=vector,
                    payload={"content": content, "chunk_id": id, **metadata},
                )
            ],
        )

    async def delete(self, id: str) -> None:
        from qdrant_client.models import PointIdsList
        client = self._get_client()
        await client.delete(
            collection_name=self._collection,
            points_selector=PointIdsList(points=[self._point_id(id)]),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_vector_search_service() -> VectorSearchProtocol:
    from app.config import settings
    if settings.use_mock_vector_search:
        logger.info("VectorSearch: using MockVectorSearch")
        return MockVectorSearch()
    logger.info("VectorSearch: connecting to Qdrant at %s", settings.qdrant_url)
    return QdrantVectorSearch(settings.qdrant_url, settings.qdrant_collection, settings.qdrant_api_key)

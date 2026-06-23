from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingProtocol(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class MockEmbeddingService:
    """Returns zero vectors. Lets the full pipeline run without a model download."""

    _DIM = 384

    def embed_text(self, text: str) -> list[float]:
        return [0.0] * self._DIM

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._DIM for _ in texts]


class FastEmbedService:
    """Real embeddings via fastembed (langchain-community wrapper).

    Lazy-initialised so the import never crashes if the model isn't cached.
    Install: pip install fastembed
    """

    _MODEL = "BAAI/bge-small-en-v1.5"

    def __init__(self) -> None:
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from langchain_community.embeddings import FastEmbedEmbeddings
                self._embedder = FastEmbedEmbeddings(model_name=self._MODEL)
            except Exception as exc:
                raise RuntimeError(
                    f"FastEmbedService could not initialise ({exc}). "
                    "Run: pip install fastembed"
                ) from exc
        return self._embedder

    def embed_text(self, text: str) -> list[float]:
        return self._get_embedder().embed_query(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._get_embedder().embed_documents(texts)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

import os


def get_embedding_service() -> EmbeddingProtocol:
    use_mock = os.getenv("USE_MOCK_VECTOR_SEARCH", "true").lower() not in ("false", "0", "no")
    if use_mock:
        logger.info("EmbeddingService: using MockEmbeddingService")
        return MockEmbeddingService()
    logger.info("EmbeddingService: using FastEmbedService")
    return FastEmbedService()

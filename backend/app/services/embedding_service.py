from __future__ import annotations

import hashlib
import logging
import math
import re
from functools import lru_cache
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


_STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its", "of", "on", "or", "she", "that", "the", "their", "them", "they", "this", "to", "was", "were", "what", "when", "where", "which", "who", "whom", "why", "will", "with", "you", "your", "do", "does", "did", "how", "about", "can", "could", "should", "would", "tell", "me", "my", "us", "we", "our"]
)


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for w in words:
        if w in _STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]  # crude plural folding: "skills" ~ "skill"
        out.append(w)
    return out


class HashingEmbeddingService:
    """Offline embeddings: hashed unigram+bigram term counts, L2-normalised.

    Needs no model download. Retrieval is keyword-overlap based (no synonym
    understanding), which is plenty for asking questions about a few uploaded
    documents. Hashing is deterministic (md5), so vectors are stable across runs.
    """

    _DIM = 384

    def embed_text(self, text: str) -> list[float]:
        toks = _tokens(text)
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:], strict=False)]
        vec = [0.0] * self._DIM
        for f in feats:
            h = int.from_bytes(hashlib.md5(f.encode(), usedforsecurity=False).digest()[:8], "big")
            # Unsigned: with only 384 buckets, random +/- signs let collisions
            # cancel real matches; unsigned collisions can only add noise.
            vec[h % self._DIM] += 1.0
        # sublinear scaling keeps long pages from dominating, then normalise
        vec = [math.log1p(v) for v in vec]
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


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

@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingProtocol:
    from app.config import settings
    if settings.use_mock_vector_search:
        logger.info("EmbeddingService: using MockEmbeddingService")
        return MockEmbeddingService()
    if settings.embedding_provider == "hash":
        logger.info("EmbeddingService: using HashingEmbeddingService")
        return HashingEmbeddingService()
    logger.info("EmbeddingService: using FastEmbedService")
    return FastEmbedService()

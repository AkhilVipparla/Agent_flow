from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from app.schemas.search import WebSearchResult

logger = logging.getLogger(__name__)


@runtime_checkable
class WebSearchProtocol(Protocol):
    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]: ...


# ---------------------------------------------------------------------------
# Mock — deterministic results; no network or API key required.
# ---------------------------------------------------------------------------

_MOCK_RESULTS: list[WebSearchResult] = [
    WebSearchResult(
        title="Global AI Market Report 2025 — Industry Analysis",
        url="https://example-research.com/ai-market-2025",
        snippet=(
            "The global AI market is projected to reach $1.3 trillion by 2030, growing at a CAGR of 38%. "
            "Enterprise adoption accelerated significantly in 2024, with 67% of Fortune 500 companies "
            "deploying production AI systems, up from 42% in 2023."
        ),
    ),
    WebSearchResult(
        title="Enterprise RAG Systems: Benchmarks and Best Practices",
        url="https://example-tech.com/enterprise-rag-benchmarks",
        snippet=(
            "Retrieval-Augmented Generation systems in enterprise settings achieve 91% accuracy on "
            "domain-specific queries when paired with curated knowledge bases. Latency benchmarks "
            "show median response times of 1.8 seconds for 7B parameter models on A100 hardware."
        ),
    ),
    WebSearchResult(
        title="LangGraph Multi-Agent Orchestration — Developer Guide",
        url="https://example-docs.com/langgraph-multi-agent",
        snippet=(
            "LangGraph enables stateful multi-agent workflows with built-in support for cycles, "
            "branching, and human-in-the-loop checkpoints. Production deployments typically combine "
            "3–7 specialised agents, reducing hallucination rates by 54% compared to single-agent systems."
        ),
    ),
    WebSearchResult(
        title="Vector Database Comparison: Qdrant vs Pinecone vs Weaviate 2025",
        url="https://example-blog.com/vector-db-comparison-2025",
        snippet=(
            "Qdrant leads in filtered search performance at scale, handling 10M+ vectors with sub-10ms "
            "P99 latency. Pinecone remains the easiest to operate as a managed service. Weaviate offers "
            "the richest hybrid search capabilities for mixed structured and unstructured workloads."
        ),
    ),
    WebSearchResult(
        title="Groq LPU Inference Speed: Real-World Enterprise Results",
        url="https://example-news.com/groq-enterprise-inference",
        snippet=(
            "Groq's Language Processing Unit achieves 750 tokens per second on Llama 3 70B, "
            "approximately 10× faster than GPU-based inference. Enterprise customers report "
            "cost reductions of 40–60% for high-volume query workloads compared to OpenAI API pricing."
        ),
    ),
]


class MockWebSearch:
    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        return _MOCK_RESULTS[:max_results]


# ---------------------------------------------------------------------------
# Real — Tavily via langchain-community; lazy init.
# ---------------------------------------------------------------------------

class TavilyWebSearch:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._wrapper = None

    def _get_wrapper(self):
        if self._wrapper is None:
            from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
            self._wrapper = TavilySearchAPIWrapper(tavily_api_key=self._api_key)
        return self._wrapper

    async def search(self, query: str, max_results: int = 5) -> list[WebSearchResult]:
        try:
            wrapper = self._get_wrapper()
            raw = await wrapper.results_async(query, max_results=max_results)
            return [
                WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                )
                for item in raw
            ]
        except Exception as exc:
            logger.warning("TavilyWebSearch failed: %s — returning empty results", exc)
            return []


# ---------------------------------------------------------------------------
# Factory + public callable used by agents.
# ---------------------------------------------------------------------------

_tool: WebSearchProtocol | None = None


def get_web_search_tool() -> WebSearchProtocol:
    from app.config import settings
    if settings.use_mock_search:
        logger.info("WebSearchTool: using MockWebSearch")
        return MockWebSearch()
    logger.info("WebSearchTool: using TavilyWebSearch")
    return TavilyWebSearch(api_key=settings.tavily_api_key)


async def web_search(query: str, max_results: int = 5) -> list[WebSearchResult]:
    """Public callable for agents. Never call search APIs directly — use this."""
    global _tool
    if _tool is None:
        _tool = get_web_search_tool()
    return await _tool.search(query, max_results=max_results)

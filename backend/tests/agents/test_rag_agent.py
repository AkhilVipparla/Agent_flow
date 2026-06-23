from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.rag_agent import RAGAgent
from app.graph.state import initial_state
from app.services.qdrant_service import SearchResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYNTHESISED = "Q4 revenue reached $142M, a 23% year-over-year increase driven by SaaS growth."

_MOCK_RESULTS = [
    SearchResult(
        id="doc-001-chunk-1",
        content="Q4 2024 revenue reached $142M, up 23% YoY. Gross margin improved to 68%.",
        score=0.97,
        metadata={"source": "Q4 2024 Earnings Report", "url": None, "page": 4},
    ),
    SearchResult(
        id="doc-002-chunk-1",
        content="Operating income was $53M. Operating expenses totalled $89M in Q4 2024.",
        score=0.91,
        metadata={"source": "Q4 2024 Earnings Report", "url": None, "page": 5},
    ),
]


def _make_agent(llm_response: str = _SYNTHESISED) -> RAGAgent:
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = llm_response
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("app.agents.base_agent.get_llm", return_value=mock_llm):
        agent = RAGAgent()

    return agent


def _state() -> dict:
    return initial_state("What were the Q4 revenue results?")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieved_documents_set_in_state():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent()
        result = await agent.run(_state())

    assert "retrieved_documents" in result
    assert len(result["retrieved_documents"]) == 1


@pytest.mark.asyncio
async def test_citations_appended_to_state():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent()
        result = await agent.run(_state())

    assert "citations" in result
    assert len(result["citations"]) == len(_MOCK_RESULTS)


@pytest.mark.asyncio
async def test_vector_search_tool_called():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS) as mock_search:
        agent = _make_agent()
        await agent.run(_state())

    mock_search.assert_called_once_with("What were the Q4 revenue results?", top_k=5)


@pytest.mark.asyncio
async def test_llm_synthesizes_content():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent(llm_response=_SYNTHESISED)
        result = await agent.run(_state())

    evidence = result["retrieved_documents"][0]
    assert evidence.content == _SYNTHESISED


@pytest.mark.asyncio
async def test_empty_results_returns_no_update():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=[]):
        agent = _make_agent()
        result = await agent.run(_state())

    assert result == {}


@pytest.mark.asyncio
async def test_citation_source_from_metadata():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent()
        result = await agent.run(_state())

    sources = [c.source for c in result["citations"]]
    assert all(s == "Q4 2024 Earnings Report" for s in sources)


@pytest.mark.asyncio
async def test_citation_page_from_metadata():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent()
        result = await agent.run(_state())

    pages = [c.page for c in result["citations"]]
    assert pages == [4, 5]


@pytest.mark.asyncio
async def test_evidence_item_agent_is_rag():
    with patch("app.agents.rag_agent.vector_search", new_callable=AsyncMock, return_value=_MOCK_RESULTS):
        agent = _make_agent()
        result = await agent.run(_state())

    assert result["retrieved_documents"][0].agent == "rag"

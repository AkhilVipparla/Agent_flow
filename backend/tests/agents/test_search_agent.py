from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.search_agent import SearchAgent
from app.graph.state import initial_state
from app.schemas.search import LLMSearchAnalysis, WebSearchResult

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MOCK_RESULTS = [
    WebSearchResult(
        title="AI Market Report 2025",
        url="https://example.com/ai-market",
        snippet="The AI market is projected to reach $1.3 trillion by 2030.",
    ),
    WebSearchResult(
        title="Enterprise RAG Benchmarks",
        url="https://example.com/rag-benchmarks",
        snippet="RAG systems achieve 91% accuracy on domain-specific queries.",
    ),
    WebSearchResult(
        title="LangGraph Orchestration Guide",
        url="https://example.com/langgraph",
        snippet="LangGraph reduces hallucination rates by 54% in multi-agent systems.",
    ),
]

MOCK_ANALYSIS = LLMSearchAnalysis(
    findings=[
        "The AI market is expected to reach $1.3 trillion by 2030 with 38% CAGR.",
        "Enterprise RAG systems achieve 91% accuracy paired with curated knowledge bases.",
        "LangGraph multi-agent systems reduce hallucination rates by 54%.",
    ],
    confidence=0.85,
)


def _make_agent() -> SearchAgent:
    """Build a SearchAgent with a fully mocked LLM."""
    mock_llm = MagicMock()
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=MOCK_ANALYSIS)
    mock_llm.with_structured_output = MagicMock(return_value=structured_llm)

    with patch("app.agents.base_agent.get_llm", return_value=mock_llm):
        agent = SearchAgent()

    return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_search_results():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    assert "search_results" in result
    assert len(result["search_results"]) == 1


@pytest.mark.asyncio
async def test_output_has_required_keys():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    entry = result["search_results"][0]
    assert "findings" in entry
    assert "sources" in entry
    assert "citations" in entry
    assert "confidence" in entry


@pytest.mark.asyncio
async def test_findings_are_non_empty():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    findings = result["search_results"][0]["findings"]
    assert isinstance(findings, list)
    assert len(findings) > 0
    assert all(isinstance(f, str) and f for f in findings)


@pytest.mark.asyncio
async def test_citations_carry_urls():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    citations = result["citations"]
    assert len(citations) == len(MOCK_RESULTS)
    for citation in citations:
        assert citation.url is not None
        assert citation.url.startswith("http")


@pytest.mark.asyncio
async def test_confidence_in_valid_range():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    confidence = result["search_results"][0]["confidence"]
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_empty_search_returns_no_update():
    agent = _make_agent()
    state = initial_state("obscure query with no results")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=[])):
        result = await agent.run(state)

    assert result == {}


@pytest.mark.asyncio
async def test_citations_written_to_state():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    assert "citations" in result
    assert len(result["citations"]) > 0


@pytest.mark.asyncio
async def test_sources_match_search_results():
    agent = _make_agent()
    state = initial_state("What is the state of enterprise AI in 2025?")

    with patch("app.agents.search_agent.web_search", new=AsyncMock(return_value=MOCK_RESULTS)):
        result = await agent.run(state)

    sources = result["search_results"][0]["sources"]
    assert len(sources) == len(MOCK_RESULTS)
    returned_urls = {s["url"] for s in sources}
    expected_urls = {r.url for r in MOCK_RESULTS}
    assert returned_urls == expected_urls

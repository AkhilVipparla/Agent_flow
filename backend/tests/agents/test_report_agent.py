from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.report_agent import ReportAgent
from app.graph.state import initial_state
from app.schemas.agents import Citation, EvidenceItem, ExecutionPlan
from app.schemas.report import LLMReportContent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUMMARY = "Q4 revenue reached $142M, up 23% YoY, driven by strong enterprise sales."
_FINDINGS = [
    "Revenue grew 23% year-over-year to $142M in Q4.",
    "Enterprise segment accounted for 68% of total revenue.",
    "Market expanded 38% industrywide, outpacing company growth.",
]


def _make_agent(llm_output: LLMReportContent) -> ReportAgent:
    mock_llm = MagicMock()
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=llm_output)
    mock_llm.with_structured_output = MagicMock(return_value=structured_llm)

    with patch("app.agents.base_agent.get_llm", return_value=mock_llm):
        agent = ReportAgent()

    return agent


def _llm_output() -> LLMReportContent:
    return LLMReportContent(executive_summary=_SUMMARY, key_findings=_FINDINGS)


def _citation() -> Citation:
    return Citation(source="Q4 Earnings Report", url="https://example.com/q4", excerpt="Revenue reached $142M.")


def _state_with_evidence() -> dict:
    state = initial_state("What were the Q4 revenue results and market outlook?")
    state["execution_plan"] = ExecutionPlan(
        agents=["rag", "sql", "search"],
        reasoning="Query requires documents, data, and external context.",
    )
    state["retrieved_documents"] = [
        EvidenceItem(agent="rag", content="Q4 revenue reached $142M, up 23% YoY.", citations=[_citation()])
    ]
    state["sql_results"] = [
        {"query": "SELECT SUM(revenue) FROM quarters WHERE quarter='Q4'", "rows": [], "summary": "Total Q4 revenue: $142M.", "row_count": 1}
    ]
    state["search_results"] = [
        {"findings": ["Market grew 38% in 2024."], "sources": [], "citations": [], "confidence": 0.85}
    ]
    state["citations"] = [_citation()]
    state["confidence_score"] = 0.88
    return state


def _state_empty() -> dict:
    state = initial_state("What were the Q4 revenue results?")
    state["confidence_score"] = 0.5
    return state


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_final_report_set_in_state():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_evidence())

    assert "final_report" in result
    assert result["final_report"] != ""


@pytest.mark.asyncio
async def test_report_json_has_required_keys():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_evidence())

    report = json.loads(result["final_report"])
    assert "executive_summary" in report
    assert "key_findings" in report
    assert "citations" in report
    assert "confidence_score" in report


@pytest.mark.asyncio
async def test_executive_summary_from_llm():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_evidence())

    report = json.loads(result["final_report"])
    assert report["executive_summary"] == _SUMMARY


@pytest.mark.asyncio
async def test_key_findings_from_llm():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_evidence())

    report = json.loads(result["final_report"])
    assert report["key_findings"] == _FINDINGS


@pytest.mark.asyncio
async def test_citations_from_state_preserved():
    agent = _make_agent(_llm_output())
    state = _state_with_evidence()
    result = await agent.run(state)

    report = json.loads(result["final_report"])
    assert len(report["citations"]) == len(state["citations"])
    assert report["citations"][0]["source"] == _citation().source


@pytest.mark.asyncio
async def test_confidence_from_state():
    agent = _make_agent(_llm_output())
    state = _state_with_evidence()
    result = await agent.run(state)

    report = json.loads(result["final_report"])
    assert report["confidence_score"] == pytest.approx(state["confidence_score"])


@pytest.mark.asyncio
async def test_empty_evidence_produces_report():
    agent = _make_agent(LLMReportContent(executive_summary="Insufficient data.", key_findings=[]))
    result = await agent.run(_state_empty())

    assert "final_report" in result
    report = json.loads(result["final_report"])
    assert report["executive_summary"] == "Insufficient data."
    assert report["key_findings"] == []
    assert report["citations"] == []


@pytest.mark.asyncio
async def test_report_does_not_write_evidence_fields():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_evidence())

    evidence_keys = {"retrieved_documents", "sql_results", "search_results", "file_results"}
    assert evidence_keys.isdisjoint(result.keys())

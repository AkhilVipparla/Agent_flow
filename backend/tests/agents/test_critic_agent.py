from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.critic_agent import CriticAgent
from app.graph.state import initial_state
from app.schemas.agents import Citation, EvidenceItem, ExecutionPlan
from app.schemas.critic import CriticOutput

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(llm_output: CriticOutput) -> CriticAgent:
    mock_llm = MagicMock()
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=llm_output)
    mock_llm.with_structured_output = MagicMock(return_value=structured_llm)

    with patch("app.agents.base_agent.get_llm", return_value=mock_llm):
        agent = CriticAgent()

    return agent


def _evidence_item(content: str = "Test evidence content.") -> EvidenceItem:
    return EvidenceItem(
        agent="rag",
        content=content,
        citations=[Citation(source="Test Doc", excerpt="excerpt")],
    )


def _state_with_evidence() -> dict:
    state = initial_state("What were the Q4 revenue results and market outlook?")
    state["execution_plan"] = ExecutionPlan(
        agents=["rag", "sql", "search"],
        reasoning="Query requires documents, data, and external context.",
    )
    state["retrieved_documents"] = [_evidence_item("Q4 revenue reached $142M, up 23% YoY.")]
    state["sql_results"] = [{"query": "SELECT ...", "rows": [], "summary": "5 reports created in Q4.", "row_count": 0}]
    state["search_results"] = [{"findings": ["Market grew 38% in 2024."], "sources": [], "citations": [], "confidence": 0.85}]
    return state


def _state_empty() -> dict:
    state = initial_state("What were the Q4 revenue results?")
    state["execution_plan"] = ExecutionPlan(
        agents=["rag", "sql"],
        reasoning="Query requires documents and data.",
    )
    return state


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pass_with_sufficient_evidence():
    output = CriticOutput(decision="PASS", confidence=0.88, reason="All planned agents returned relevant evidence.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert result["critic_decision"] == "PASS"


@pytest.mark.asyncio
async def test_retry_with_no_evidence():
    output = CriticOutput(
        decision="RETRY",
        confidence=0.2,
        reason="No evidence was collected from any agent.",
        missing_information=["Q4 financial data", "external market context"],
    )
    agent = _make_agent(output)
    result = await agent.run(_state_empty())

    assert result["critic_decision"] == "RETRY"


@pytest.mark.asyncio
async def test_retry_with_low_confidence():
    output = CriticOutput(
        decision="RETRY",
        confidence=0.35,
        reason="Evidence is too vague to support a reliable report.",
        missing_information=["Specific revenue figures"],
    )
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert result["critic_decision"] == "RETRY"
    assert result["confidence_score"] == pytest.approx(0.35)


@pytest.mark.asyncio
async def test_force_pass_at_max_retries():
    """LLM says RETRY but retry_count has hit the ceiling — must be overridden to PASS."""
    output = CriticOutput(
        decision="RETRY",
        confidence=0.4,
        reason="Evidence still insufficient.",
        missing_information=["More data needed"],
    )
    agent = _make_agent(output)

    state = _state_empty()
    state["retry_count"] = 2  # equals settings.max_retry_count default

    result = await agent.run(state)

    assert result["critic_decision"] == "PASS"
    assert "[Max retries reached]" in result["critic_feedback"]


@pytest.mark.asyncio
async def test_confidence_written_to_state():
    output = CriticOutput(decision="PASS", confidence=0.91, reason="Strong evidence from all sources.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert "confidence_score" in result
    assert result["confidence_score"] == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_decision_written_to_state():
    output = CriticOutput(decision="PASS", confidence=0.80, reason="Sufficient evidence collected.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert "critic_decision" in result
    assert result["critic_decision"] in ("PASS", "RETRY")


@pytest.mark.asyncio
async def test_retry_increments_retry_count():
    output = CriticOutput(
        decision="RETRY",
        confidence=0.3,
        reason="Evidence gaps remain.",
        missing_information=["SQL data missing"],
    )
    agent = _make_agent(output)

    state = _state_empty()
    state["retry_count"] = 0
    result = await agent.run(state)

    assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_pass_does_not_increment_retry_count():
    output = CriticOutput(decision="PASS", confidence=0.85, reason="Evidence is complete.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert "retry_count" not in result


@pytest.mark.asyncio
async def test_missing_information_in_feedback_on_retry():
    output = CriticOutput(
        decision="RETRY",
        confidence=0.25,
        reason="Key data is absent.",
        missing_information=["Q4 revenue breakdown", "Competitor pricing data"],
    )
    agent = _make_agent(output)
    result = await agent.run(_state_empty())

    assert "critic_feedback" in result
    assert "Q4 revenue breakdown" in result["critic_feedback"]
    assert "Competitor pricing data" in result["critic_feedback"]


@pytest.mark.asyncio
async def test_confidence_clamped_above_one():
    """Validator must silently clamp any out-of-range LLM output."""
    output = CriticOutput(decision="PASS", confidence=1.5, reason="Overconfident LLM.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert result["confidence_score"] <= 1.0


@pytest.mark.asyncio
async def test_feedback_written_on_pass():
    output = CriticOutput(decision="PASS", confidence=0.9, reason="All sources corroborate the query.")
    agent = _make_agent(output)
    result = await agent.run(_state_with_evidence())

    assert "critic_feedback" in result
    assert result["critic_feedback"] != ""

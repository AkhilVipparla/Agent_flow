from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.graph.state import AgentState, increment_retry, update_critic_result
from app.schemas.critic import CriticOutput

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a critical evaluator for an enterprise research workflow. Your sole responsibility \
is to assess the quality and completeness of evidence collected by other agents.

You must NOT generate answers, summaries, or final reports.
You must NOT call any tools.
You must ONLY evaluate whether the collected evidence is sufficient to answer the query.

Evaluation criteria:
- Relevance: Does the evidence directly address the research query?
- Coverage: Are all aspects of the query addressed by at least one evidence source?
- Specificity: Is the evidence concrete (facts, numbers, citations) rather than vague?
- Conflict: Does contradictory evidence exist that cannot be resolved?
- Gaps: Are there planned agents that returned no evidence?

Scoring guide:
- 0.9–1.0: Comprehensive, specific, directly relevant evidence from multiple sources.
- 0.7–0.89: Mostly relevant with minor gaps; sufficient to write a reliable report.
- 0.5–0.69: Partial coverage; important aspects of the query are unaddressed.
- 0.3–0.49: Sparse or vague evidence; a retry is likely to improve quality.
- 0.0–0.29: Little to no useful evidence collected.

Decision rule:
- PASS if confidence >= {threshold} or max retries reached./cl
- RETRY if confidence < {threshold} and evidence gaps can be addressed by replanning.

Return only structured JSON matching the required schema.
"""

_USER_PROMPT = """\
Research Query: {query}

Planned Agents: {planned_agents}
Agents with NO evidence returned: {empty_agents}

--- Evidence Collected ---

[Enterprise Documents — RAG Agent]
{rag_evidence}

[Database Results — SQL Agent]
{sql_evidence}

[Web Search Results — Search Agent]
{search_evidence}

[File Analysis — File Agent]
{file_evidence}

Evaluate the evidence above and return your structured assessment.
"""


def _summarise_rag(items: list) -> str:
    if not items:
        return "No evidence collected."
    parts = []
    for item in items:
        content = item.content if hasattr(item, "content") else item.get("content", "")
        parts.append(content[:400])
    return "\n\n".join(parts)


def _summarise_sql(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No evidence collected."
    parts = [r.get("summary", str(r.get("rows", "")))[:400] for r in results]
    return "\n\n".join(parts)


def _summarise_search(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No evidence collected."
    parts = []
    for r in results:
        findings = r.get("findings", [])
        parts.append(" ".join(findings)[:400])
    return "\n\n".join(parts)


def _planned_agents(state: AgentState) -> list[str]:
    plan = state.get("execution_plan")
    if plan is None:
        return []
    agents = plan.agents if hasattr(plan, "agents") else plan.get("agents", [])
    return list(agents)


def _empty_agents(state: AgentState, planned: list[str]) -> list[str]:
    evidence_map = {
        "rag":    bool(state["retrieved_documents"]),
        "sql":    bool(state["sql_results"]),
        "search": bool(state["search_results"]),
        "file":   bool(state["file_results"]),
    }
    return [a for a in planned if not evidence_map.get(a, True)]


class CriticAgent(BaseAgent):
    name = "critic"

    def __init__(self) -> None:
        super().__init__()
        self._structured_llm = self._llm.with_structured_output(CriticOutput)

    async def run(self, state: AgentState) -> dict[str, Any]:
        planned = _planned_agents(state)
        empty = _empty_agents(state, planned)

        messages = [
            (
                "system",
                _SYSTEM_PROMPT.format(threshold=settings.confidence_threshold),
            ),
            (
                "human",
                _USER_PROMPT.format(
                    query=state["query"],
                    planned_agents=", ".join(planned) if planned else "none",
                    empty_agents=", ".join(empty) if empty else "none",
                    rag_evidence=_summarise_rag(state["retrieved_documents"]),
                    sql_evidence=_summarise_sql(state["sql_results"]),
                    search_evidence=_summarise_search(state["search_results"]),
                    file_evidence=_summarise_rag(state["file_results"]),
                ),
            ),
        ]

        output: CriticOutput = await self._structured_llm.ainvoke(messages)

        # Guard: force PASS if max retries exhausted to prevent infinite loops.
        if output.decision == "RETRY" and state["retry_count"] >= settings.max_retry_count:
            logger.warning(
                "CriticAgent: max retries (%d) reached — forcing PASS with confidence %.2f",
                settings.max_retry_count,
                output.confidence,
            )
            output = CriticOutput(
                decision="PASS",
                confidence=output.confidence,
                reason=f"[Max retries reached] {output.reason}",
                missing_information=output.missing_information,
            )

        feedback = output.reason
        if output.missing_information:
            gaps = "; ".join(output.missing_information)
            feedback = f"{feedback} Missing: {gaps}"

        result = update_critic_result(
            decision=output.decision,
            confidence=output.confidence,
            feedback=feedback,
        )

        if output.decision == "RETRY":
            result.update(increment_retry(state["retry_count"]))

        return result

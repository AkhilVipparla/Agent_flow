from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, update_final_report
from app.schemas.report import LLMReportContent, ReportOutput

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a senior research analyst writing the final report for an enterprise research workflow.

Your sole responsibility is to synthesise the evidence provided into a clear, professional report.

Rules:
- Do NOT retrieve additional information.
- Do NOT call any tools.
- Do NOT invent facts not present in the evidence.
- Write an executive summary (3–5 sentences) that directly answers the research query.
- List key findings as specific, evidence-backed statements. Each finding is one sentence.
- Omit findings that are vague or unsupported by the evidence.

Return only structured JSON matching the required schema.
"""

_USER_PROMPT = """\
Research Query: {query}

--- Evidence ---

[Enterprise Documents — RAG Agent]
{rag_evidence}

[Database Results — SQL Agent]
{sql_evidence}

[Web Search Results — Search Agent]
{search_evidence}

[File Analysis — File Agent]
{file_evidence}

Synthesise the evidence above into an executive summary and key findings.
"""


def _summarise_rag(items: list) -> str:
    if not items:
        return "No documents retrieved."
    parts = []
    for item in items:
        content = item.content if hasattr(item, "content") else item.get("content", "")
        parts.append(content[:500])
    return "\n\n".join(parts)


def _summarise_sql(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No database results."
    parts = [r.get("summary", str(r.get("rows", "")))[:500] for r in results]
    return "\n\n".join(parts)


def _summarise_search(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No search results."
    parts = []
    for r in results:
        findings = r.get("findings", [])
        parts.append(" ".join(findings)[:500])
    return "\n\n".join(parts)


class ReportAgent(BaseAgent):
    name = "report"

    def __init__(self) -> None:
        super().__init__()
        self._structured_llm = self._llm.with_structured_output(LLMReportContent)

    async def run(self, state: AgentState) -> dict[str, Any]:
        messages = [
            ("system", _SYSTEM_PROMPT),
            (
                "human",
                _USER_PROMPT.format(
                    query=state["query"],
                    rag_evidence=_summarise_rag(state["retrieved_documents"]),
                    sql_evidence=_summarise_sql(state["sql_results"]),
                    search_evidence=_summarise_search(state["search_results"]),
                    file_evidence=_summarise_rag(state["file_results"]),
                ),
            ),
        ]

        content: LLMReportContent = await self._structured_llm.ainvoke(messages)

        report = ReportOutput(
            executive_summary=content.executive_summary,
            key_findings=content.key_findings,
            citations=state["citations"],
            confidence_score=state["confidence_score"],
        )

        return update_final_report(report.model_dump_json())

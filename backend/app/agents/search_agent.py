from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, append_citations, append_search_results
from app.schemas.agents import Citation
from app.schemas.search import LLMSearchAnalysis, SearchOutput, WebSearchResult
from app.tools.web_search_tool import web_search

logger = logging.getLogger(__name__)

_ANALYSIS_SYSTEM = """\
You are a research analyst evaluating web search results for an enterprise research query.

Given the query and a set of search result snippets, your tasks are:
1. For each snippet that contributes useful information, write one concise sentence summarising its key finding.
   Skip snippets that are irrelevant, duplicates, or too vague to be useful.
2. Score your overall confidence in the retrieved information from 0.0 to 1.0:
   - 1.0: Multiple high-quality, specific, directly relevant sources.
   - 0.7: Relevant sources but some gaps or vagueness.
   - 0.4: Partial relevance or limited specificity.
   - 0.1: Mostly irrelevant or no actionable information.

Return only structured JSON matching the required schema.
"""

_ANALYSIS_USER = """\
Research query: {query}

Search results:
{formatted_results}
"""


def _format_results(results: list[WebSearchResult]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.title}\nURL: {r.url}\nSnippet: {r.snippet}")
    return "\n\n".join(lines)


def _build_citations(results: list[WebSearchResult]) -> list[Citation]:
    return [
        Citation(
            source=r.title,
            url=r.url,
            page=None,
            excerpt=r.snippet[:300],
        )
        for r in results
    ]


class SearchAgent(BaseAgent):
    name = "search"

    def __init__(self) -> None:
        super().__init__()
        self._structured_llm = self._llm.with_structured_output(LLMSearchAnalysis)

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        results = await web_search(query, max_results=5)

        if not results:
            logger.warning("SearchAgent: no results returned for query: %r", query)
            return {}

        messages = [
            ("system", _ANALYSIS_SYSTEM),
            (
                "human",
                _ANALYSIS_USER.format(
                    query=query,
                    formatted_results=_format_results(results),
                ),
            ),
        ]

        analysis: LLMSearchAnalysis = await self._structured_llm.ainvoke(messages)

        citations = _build_citations(results)

        output = SearchOutput(
            findings=analysis.findings,
            sources=results,
            citations=citations,
            confidence=analysis.confidence,
        )

        return {
            **append_search_results([output.model_dump()]),
            **append_citations(citations),
        }

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

Return only a single JSON object matching exactly this schema (no markdown fences, no extra text):
{"findings": ["<one sentence per useful source>", ...], "confidence": <float 0.0-1.0>}
"""

_ANALYSIS_USER = """\
Research query: {query}

Search results:
{formatted_results}
"""


# Long page excerpts add cost, not insight. Providers meter tokens per minute, and one
# research run already makes many model calls, so keep what is sent for analysis short.
_SNIPPET_CHARS = 600


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def _format_results(results: list[WebSearchResult]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] {r.title}{chr(10)}URL: {r.url}{chr(10)}Snippet: {_clip(r.snippet, _SNIPPET_CHARS)}"
        )
    return (chr(10) * 2).join(lines)


def _unsummarised(results: list[WebSearchResult]) -> LLMSearchAnalysis:
    """Findings taken straight from the pages, for when the model cannot summarise them."""
    return LLMSearchAnalysis(
        findings=[f"{r.title}: {_clip(r.snippet, 220)}" for r in results if r.snippet],
        confidence=0.4,
    )


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

    @property
    def _structured_llm(self):
        return self._llm.with_structured_output(LLMSearchAnalysis, method="json_mode")

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        results = await web_search(query, max_results=5)

        if not results:
            logger.warning("SearchAgent: no results returned for query: %r", query)
            return {"warnings": ["Web search returned no results. Check your Tavily key in Settings."]}

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

        warnings: list[str] = []
        try:
            analysis: LLMSearchAnalysis = await self._structured_llm.ainvoke(messages)
        except Exception as exc:
            # The pages were found; only the model's summary failed (often a provider rate
            # limit). Keep the sources rather than discard a search that already cost a call.
            logger.warning("SearchAgent: could not summarise results (%s)", type(exc).__name__)
            analysis = _unsummarised(results)
            warnings.append(
                "Web results were found, but your model could not summarise them "
                "(it may be rate limited), so they are shown unsummarised."
            )

        citations = _build_citations(results)

        output = SearchOutput(
            findings=analysis.findings,
            sources=results,
            citations=citations,
            confidence=analysis.confidence,
        )

        update = {
            **append_search_results([output.model_dump()]),
            **append_citations(citations),
        }
        if warnings:
            update["warnings"] = warnings
        return update

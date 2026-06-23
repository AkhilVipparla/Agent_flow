from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, append_citations, append_retrieved_documents
from app.schemas.agents import Citation, EvidenceItem
from app.services.qdrant_service import SearchResult
from app.tools.vector_search_tool import vector_search

logger = logging.getLogger(__name__)

_SYNTHESIS_SYSTEM = """\
You are an enterprise research assistant. You have been given a set of retrieved \
document passages relevant to a user query. Your task is to synthesise these passages \
into a single, concise evidence summary (3-5 sentences) that directly addresses the query.

Rules:
- Only use information present in the passages. Do not add external knowledge.
- Preserve all specific facts, numbers, and dates from the source material.
- Write in third-person, objective prose.
- Do not mention that you are summarising passages.
"""

_SYNTHESIS_USER = """\
Query: {query}

Retrieved passages:
{passages}

Synthesise the evidence above into a concise summary that addresses the query.
"""


def _build_citations(results: list[SearchResult]) -> list[Citation]:
    return [
        Citation(
            source=r.metadata.get("source", r.id),
            url=r.metadata.get("url"),
            page=r.metadata.get("page"),
            excerpt=r.content[:300],
        )
        for r in results
    ]


def _format_passages(results: list[SearchResult]) -> str:
    return "\n\n".join(
        f"[{r.metadata.get('source', r.id)}]\n{r.content}" for r in results
    )


class RAGAgent(BaseAgent):
    name = "rag"

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        results: list[SearchResult] = await vector_search(query, top_k=5)

        if not results:
            logger.warning("RAGAgent: no documents retrieved for query: %r", query)
            return {}

        citations = _build_citations(results)
        passages = _format_passages(results)

        messages = [
            ("system", _SYNTHESIS_SYSTEM),
            ("human", _SYNTHESIS_USER.format(query=query, passages=passages)),
        ]
        response = await self._llm.ainvoke(messages)

        final_evidence = EvidenceItem(
            agent="rag",
            content=response.content,
            citations=citations,
        )

        return {
            **append_retrieved_documents([final_evidence]),
            **append_citations(citations),
        }

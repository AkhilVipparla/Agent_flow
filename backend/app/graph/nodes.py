from __future__ import annotations

import logging
from typing import Any

from app.graph.state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-initialized agent singletons.
# Agents are created on first call, not on import, so this module is safe to
# import in tests without triggering LLM or service initialization.
# ---------------------------------------------------------------------------

_planner = None
_rag = None
_sql = None
_search = None
_file = None
_critic = None
_report = None


def _get_planner():
    global _planner
    if _planner is None:
        from app.agents.planner_agent import PlannerAgent
        _planner = PlannerAgent()
    return _planner


def _get_rag():
    global _rag
    if _rag is None:
        from app.agents.rag_agent import RAGAgent
        _rag = RAGAgent()
    return _rag


def _get_sql():
    global _sql
    if _sql is None:
        from app.agents.sql_agent import SQLAgent
        _sql = SQLAgent()
    return _sql


def _get_search():
    global _search
    if _search is None:
        from app.agents.search_agent import SearchAgent
        _search = SearchAgent()
    return _search


def _get_file():
    global _file
    if _file is None:
        from app.agents.file_agent import FileAnalysisAgent
        _file = FileAnalysisAgent()
    return _file


def _get_critic():
    global _critic
    if _critic is None:
        from app.agents.critic_agent import CriticAgent
        _critic = CriticAgent()
    return _critic


def _get_report():
    global _report
    if _report is None:
        from app.agents.report_agent import ReportAgent
        _report = ReportAgent()
    return _report


# ---------------------------------------------------------------------------
# Node functions — one per agent.
# Each node delegates entirely to the agent; no reasoning logic lives here.
# ---------------------------------------------------------------------------

async def planner_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing planner_node")
    return await _get_planner().safe_run(state)


async def rag_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing rag_node")
    return await _get_rag().safe_run(state)


async def sql_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing sql_node")
    return await _get_sql().safe_run(state)


async def search_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing search_node")
    return await _get_search().safe_run(state)


async def file_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing file_node")
    return await _get_file().safe_run(state)


async def critic_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing critic_node")
    return await _get_critic().safe_run(state)


async def report_node(state: AgentState) -> dict[str, Any]:
    logger.debug("Executing report_node")
    return await _get_report().safe_run(state)

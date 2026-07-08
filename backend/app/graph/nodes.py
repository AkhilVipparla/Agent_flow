from __future__ import annotations

import logging
import time
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
# The wrapper times the agent and appends an execution record to
# state.agent_steps so the API can report real per-agent progress.
# ---------------------------------------------------------------------------

async def _timed_run(agent_name: str, agent, state: AgentState) -> dict[str, Any]:
    logger.debug("Executing %s node", agent_name)
    started = time.perf_counter()
    update = await agent.safe_run(state)
    duration_ms = int((time.perf_counter() - started) * 1000)
    status = "failed" if update.get("error") else "complete"
    step = {"agent_name": agent_name, "status": status, "duration_ms": duration_ms}
    return {**update, "agent_steps": [step]}


async def planner_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("planner", _get_planner(), state)


async def rag_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("rag", _get_rag(), state)


async def sql_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("sql", _get_sql(), state)


async def search_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("search", _get_search(), state)


async def file_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("file", _get_file(), state)


async def critic_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("critic", _get_critic(), state)


async def report_node(state: AgentState) -> dict[str, Any]:
    return await _timed_run("report", _get_report(), state)

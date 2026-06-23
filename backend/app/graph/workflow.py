from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    critic_node,
    file_node,
    planner_node,
    rag_node,
    report_node,
    search_node,
    sql_node,
)
from app.graph.router import route_after_critic, route_after_planner
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

# All nodes the planner can fan out to, declared explicitly so LangGraph can
# validate the graph structure at compile time.
_EVIDENCE_NODES = ("rag", "sql", "search", "file_analysis")

_PLANNER_PATH_MAP: dict[str, str] = {node: node for node in _EVIDENCE_NODES}

_CRITIC_PATH_MAP: dict[str, str] = {
    "report": "report",
    "planner": "planner",
}


def build_graph():
    """Assemble and compile the LangGraph StateGraph.

    Topology:
        START → planner → [parallel fan-out] → critic → [conditional]
            PASS  → report → END
            RETRY → planner  (retry loop; max retries enforced by CriticAgent)
    """
    builder = StateGraph(AgentState)

    # --- Nodes ---
    builder.add_node("planner", planner_node)
    builder.add_node("rag", rag_node)
    builder.add_node("sql", sql_node)
    builder.add_node("search", search_node)
    builder.add_node("file_analysis", file_node)
    builder.add_node("critic", critic_node)
    builder.add_node("report", report_node)

    # --- Entry point ---
    builder.add_edge(START, "planner")

    # --- Planner → parallel evidence agents ---
    # route_after_planner returns a list of node names; LangGraph fans out to
    # all of them simultaneously. State is merged via operator.add reducers
    # before critic runs.
    builder.add_conditional_edges("planner", route_after_planner, _PLANNER_PATH_MAP)

    # --- Evidence agents → critic (convergence point) ---
    for node in _EVIDENCE_NODES:
        builder.add_edge(node, "critic")

    # --- Critic → report (PASS) or planner (RETRY) ---
    builder.add_conditional_edges("critic", route_after_critic, _CRITIC_PATH_MAP)

    # --- Report → END ---
    builder.add_edge("report", END)

    compiled = builder.compile()
    logger.info("LangGraph StateGraph compiled successfully")
    return compiled


# Module-level singleton consumed by ResearchService.
graph = build_graph()

from __future__ import annotations

from typing import Literal

from app.graph.state import AgentState

# Maps execution_plan agent identifiers to graph node names.
# "file" is the planner's identifier; "file_analysis" is the node name.
_AGENT_TO_NODE: dict[str, str] = {
    "rag": "rag",
    "sql": "sql",
    "search": "search",
    "file": "file_analysis",
}


def route_after_planner(state: AgentState) -> list[str]:
    """Return the list of agent node names to run in parallel.

    Reads execution_plan.agents and maps each identifier to its graph node
    name. Returns ["rag"] as a fallback if the plan is missing or empty.
    Routing is purely state-driven — no business logic lives here.
    """
    plan = state.get("execution_plan")  # type: ignore[call-overload]
    if plan is None:
        return ["rag"]

    agents = plan.agents if hasattr(plan, "agents") else plan.get("agents", [])
    nodes = [_AGENT_TO_NODE[a] for a in agents if a in _AGENT_TO_NODE]
    return nodes if nodes else ["rag"]


def route_after_critic(state: AgentState) -> Literal["report", "planner"]:
    """Return 'report' on PASS, 'planner' on RETRY.

    Reads critic_decision written by CriticAgent. Defaults to 'report' — the
    max-retry guard inside CriticAgent ensures infinite loops cannot occur.
    """
    decision = state.get("critic_decision")  # type: ignore[call-overload]
    if decision == "RETRY":
        return "planner"
    return "report"

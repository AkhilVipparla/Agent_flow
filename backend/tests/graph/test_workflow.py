from __future__ import annotations

import pytest

from app.graph.router import route_after_critic, route_after_planner
from app.graph.state import initial_state
from app.schemas.agents import ExecutionPlan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_with_plan(agents: list[str]) -> dict:
    state = initial_state("What were the Q4 results?")
    state["execution_plan"] = ExecutionPlan(
        agents=agents,
        reasoning="test plan",
    )
    return state


def _state_with_decision(decision: str | None) -> dict:
    state = initial_state("test query")
    state["critic_decision"] = decision
    return state


# ---------------------------------------------------------------------------
# route_after_planner
# ---------------------------------------------------------------------------

def test_rag_only_plan():
    result = route_after_planner(_state_with_plan(["rag"]))
    assert result == ["rag"]


def test_sql_only_plan():
    result = route_after_planner(_state_with_plan(["sql"]))
    assert result == ["sql"]


def test_multiple_agents_plan():
    result = route_after_planner(_state_with_plan(["rag", "sql"]))
    assert set(result) == {"rag", "sql"}
    assert len(result) == 2


def test_file_maps_to_file_analysis_node():
    result = route_after_planner(_state_with_plan(["file"]))
    assert result == ["file_analysis"]


def test_all_agents_plan():
    result = route_after_planner(_state_with_plan(["rag", "sql", "search", "file"]))
    assert set(result) == {"rag", "sql", "search", "file_analysis"}
    assert len(result) == 4


def test_none_plan_defaults_to_rag():
    state = initial_state("test")
    # execution_plan is None by default
    result = route_after_planner(state)
    assert result == ["rag"]


def test_empty_agents_list_defaults_to_rag():
    result = route_after_planner(_state_with_plan([]))
    assert result == ["rag"]


def test_unknown_agent_names_are_ignored():
    result = route_after_planner(_state_with_plan(["rag", "unknown_agent"]))
    assert result == ["rag"]


# ---------------------------------------------------------------------------
# route_after_critic
# ---------------------------------------------------------------------------

def test_critic_pass_routes_to_report():
    result = route_after_critic(_state_with_decision("PASS"))
    assert result == "report"


def test_critic_retry_routes_to_planner():
    result = route_after_critic(_state_with_decision("RETRY"))
    assert result == "planner"


def test_critic_none_decision_defaults_to_report():
    result = route_after_critic(_state_with_decision(None))
    assert result == "report"


# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------

def test_graph_compiles():
    from app.graph.workflow import build_graph
    g = build_graph()
    assert g is not None


def test_graph_singleton_is_compiled():
    from app.graph.workflow import graph
    assert graph is not None


def test_graph_has_expected_nodes():
    from app.graph.workflow import build_graph
    g = build_graph()
    node_names = set(g.nodes)
    expected = {"planner", "rag", "sql", "search", "file_analysis", "critic", "report"}
    assert expected.issubset(node_names)

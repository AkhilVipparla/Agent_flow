from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from app.schemas.agents import Citation, EvidenceItem, ExecutionPlan


class AgentState(TypedDict):
    query: str
    execution_plan: ExecutionPlan | None
    retrieved_documents: Annotated[list[EvidenceItem], operator.add]
    sql_results: Annotated[list[dict[str, Any]], operator.add]
    search_results: Annotated[list[dict[str, Any]], operator.add]
    file_results: Annotated[list[dict[str, Any]], operator.add]
    uploaded_files: list[str]
    citations: Annotated[list[Citation], operator.add]
    confidence_score: float
    final_report: str
    retry_count: int
    error: str | None
    # Written by CriticAgent; read by the graph router and PlannerAgent on retry.
    critic_decision: str | None
    critic_feedback: str


def initial_state(query: str) -> AgentState:
    return AgentState(
        query=query,
        execution_plan=None,
        retrieved_documents=[],
        sql_results=[],
        search_results=[],
        file_results=[],
        uploaded_files=[],
        citations=[],
        confidence_score=0.0,
        final_report="",
        retry_count=0,
        error=None,
        critic_decision=None,
        critic_feedback="",
    )


def update_execution_plan(plan: ExecutionPlan) -> dict[str, Any]:
    return {"execution_plan": plan}


def update_confidence(score: float) -> dict[str, Any]:
    return {"confidence_score": score}


def update_final_report(report: str) -> dict[str, Any]:
    return {"final_report": report}


def increment_retry(current_count: int) -> dict[str, Any]:
    return {"retry_count": current_count + 1}


def set_error(message: str | None) -> dict[str, Any]:
    return {"error": message}


def append_retrieved_documents(items: list[EvidenceItem]) -> dict[str, Any]:
    return {"retrieved_documents": items}


def append_sql_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"sql_results": rows}


def append_search_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {"search_results": results}


def append_file_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {"file_results": results}


def update_uploaded_files(paths: list[str]) -> dict[str, Any]:
    return {"uploaded_files": paths}


def append_citations(citations: list[Citation]) -> dict[str, Any]:
    return {"citations": citations}


def update_critic_result(
    decision: str,
    confidence: float,
    feedback: str,
) -> dict[str, Any]:
    return {
        "critic_decision": decision,
        "confidence_score": confidence,
        "critic_feedback": feedback,
    }

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.graph.state import initial_state
from app.graph.workflow import graph
from app.schemas.common import AgentStatus
from app.schemas.research import (
    AgentRunResponse,
    AgentStepResponse,
    RunEvidence,
    SearchResultItem,
)
from app.services.postgres_service import DatabaseProtocol

logger = logging.getLogger(__name__)


def _render_report_markdown(final_report_json: str) -> tuple[str, dict[str, Any]]:
    """Convert the ReportOutput JSON written by ReportAgent into markdown.

    Returns (markdown, parsed_fields). Falls back to the raw string if it is
    not the expected JSON payload.
    """
    try:
        parsed = json.loads(final_report_json)
    except (json.JSONDecodeError, TypeError):
        return final_report_json or "", {}
    if not isinstance(parsed, dict) or "executive_summary" not in parsed:
        return final_report_json or "", {}

    lines = ["## Executive Summary", "", parsed.get("executive_summary", "")]
    findings = parsed.get("key_findings") or []
    if findings:
        lines += ["", "## Key Findings", ""]
        lines += [f"{i}. {finding}" for i, finding in enumerate(findings, 1)]
    return "\n".join(lines), parsed


def _build_evidence(result: dict[str, Any]) -> RunEvidence:
    search_items: list[SearchResultItem] = []
    for output in result.get("search_results", []):
        for source in output.get("sources", []):
            search_items.append(
                SearchResultItem(
                    title=source.get("title", ""),
                    url=source.get("url", ""),
                    snippet=source.get("snippet", ""),
                )
            )

    sql_rows: list[dict[str, Any]] = []
    for sql_output in result.get("sql_results", []):
        sql_rows.extend(sql_output.get("rows", []))

    return RunEvidence(
        retrieved_documents=result.get("retrieved_documents", []),
        sql_results=sql_rows,
        search_results=search_items,
        citations=result.get("citations", []),
        confidence_score=result.get("confidence_score", 0.0),
    )


def _build_steps(result: dict[str, Any]) -> list[AgentStepResponse]:
    evidence_counts = {
        "rag": len(result.get("retrieved_documents", [])),
        "sql": len(result.get("sql_results", [])),
        "search": len(result.get("search_results", [])),
        "file": len(result.get("file_results", [])),
    }
    return [
        AgentStepResponse(
            agent_name=step["agent_name"],
            status=AgentStatus(step.get("status", "complete")),
            duration_ms=step.get("duration_ms", 0),
            evidence_count=evidence_counts.get(step["agent_name"], 0),
        )
        for step in result.get("agent_steps", [])
    ]


async def _persist_run(run: AgentRunResponse, report_fields: dict[str, Any], db: DatabaseProtocol) -> None:
    """Write the completed run (and its report, if one was produced) to PostgreSQL."""
    try:
        await db.execute(
            """
            INSERT INTO agent_runs
                (id, query, status, agents_executed, steps, evidence,
                 final_report, confidence_score, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            (
                run.id,
                run.query,
                run.status.value,
                json.dumps(run.agents_executed),
                json.dumps([s.model_dump() for s in run.steps]),
                run.evidence.model_dump_json(),
                run.final_report,
                run.confidence_score,
                run.created_at,
            ),
        )
        if report_fields:
            await db.execute(
                """
                INSERT INTO reports
                    (id, query, executive_summary, key_findings, citations,
                     confidence_score, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                (
                    run.id,
                    run.query,
                    report_fields.get("executive_summary", ""),
                    json.dumps(report_fields.get("key_findings") or []),
                    json.dumps(report_fields.get("citations") or []),
                    run.confidence_score,
                    run.created_at,
                ),
            )
    except Exception:
        # Persistence failure must not lose the result the user is waiting on.
        logger.exception("Failed to persist run %s", run.id)


async def run_research(
    query: str,
    db: DatabaseProtocol,
    uploaded_files: list[str] | None = None,
) -> AgentRunResponse:
    run_id = str(uuid.uuid4())
    state = initial_state(query)
    if uploaded_files:
        state["uploaded_files"] = uploaded_files

    try:
        result = await graph.ainvoke(state)
        agents_executed: list[str] = []
        if result.get("execution_plan"):
            agents_executed = result["execution_plan"].agents
        status = AgentStatus.failed if result.get("error") else AgentStatus.complete
        final_report, report_fields = _render_report_markdown(result.get("final_report", ""))
        run = AgentRunResponse(
            id=run_id,
            query=query,
            agents_executed=agents_executed,
            steps=_build_steps(result),
            evidence=_build_evidence(result),
            confidence_score=result.get("confidence_score", 0.0),
            final_report=final_report,
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        await _persist_run(run, report_fields, db)
        return run
    except Exception:
        logger.exception("Research workflow failed for query=%r", query)
        return AgentRunResponse(
            id=run_id,
            query=query,
            agents_executed=[],
            confidence_score=0.0,
            final_report="",
            status=AgentStatus.failed,
            created_at=datetime.now(timezone.utc),
        )

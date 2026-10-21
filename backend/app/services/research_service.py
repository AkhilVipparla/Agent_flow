from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.config import settings
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
from app.services.request_context import current_owner

logger = logging.getLogger(__name__)


def _unique_warnings(result: dict[str, Any]) -> list[str]:
    """The run's source notes, in order, without repeats (a retry can repeat a note)."""
    seen: dict[str, None] = {}
    for note in result.get("warnings") or []:
        seen.setdefault(note, None)
    return list(seen)


def _render_report_markdown(
    final_report_json: str, warnings: list[str] | None = None
) -> tuple[str, dict[str, Any]]:
    """Convert the ReportOutput JSON written by ReportAgent into markdown.

    Returns (markdown, parsed_fields). Falls back to the raw string if it is
    not the expected JSON payload. Source problems are listed under "Data availability",
    so a gap in the evidence is stated in the report rather than hidden.
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
    if warnings:
        lines += ["", "## Data availability", ""]
        lines += [f"- {note}" for note in warnings]
        # The Reports page shows findings, not this markdown, so carry the notes there too.
        parsed = {**parsed, "key_findings": [*findings, *(f"Note: {n}" for n in warnings)]}
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


# Runs currently executing (or finished this process lifetime). Consulted before
# the database so progress is visible even when the DB is the no-op mock.
_active_runs: dict[str, AgentRunResponse] = {}
# Strong references: asyncio only keeps weak refs to tasks, so an unreferenced
# background task can be garbage-collected mid-run.
_background_tasks: set[asyncio.Task] = set()


# run id -> visitor who started it. Live runs are only visible to their owner.
_run_owner: dict[str, str] = {}


async def drain_background_runs(grace_seconds: float = 10.0) -> None:
    """On shutdown, give in-flight runs a moment to finish, then cancel the rest.

    A cancelled run is marked failed by its own error handling, so it never stays
    'running' in the database.
    """
    pending = list(_background_tasks)
    if not pending:
        return
    _, still_running = await asyncio.wait(pending, timeout=grace_seconds)
    for task in still_running:
        task.cancel()
    if still_running:
        await asyncio.wait(still_running, timeout=5)


def get_active_run(run_id: str) -> AgentRunResponse | None:
    if _run_owner.get(run_id) != current_owner():
        return None
    return _active_runs.get(run_id)


def list_active_runs() -> list[AgentRunResponse]:
    owner = current_owner()
    return [run for run_id, run in _active_runs.items() if _run_owner.get(run_id) == owner]


def count_running(owner: str | None = None) -> int:
    owner = owner or current_owner()
    return sum(
        1 for run_id, run in _active_runs.items()
        if _run_owner.get(run_id) == owner and run.status == AgentStatus.running
    )


def _progress_steps(result: dict[str, Any]) -> list[AgentStepResponse]:
    """Build the step list from a mid-run state snapshot: finished agents plus
    whichever agents are running right now."""
    steps: dict[str, AgentStepResponse] = {s.agent_name: s for s in _build_steps(result)}
    names = [s["agent_name"] for s in result.get("agent_steps", [])]

    running: list[str] = []
    if "report" in names:
        pass
    elif not names:
        running = ["planner"]
    elif names[-1] == "critic":
        running = ["planner"] if result.get("critic_decision") == "RETRY" else ["report"]
    else:
        last_planner = max((i for i, n in enumerate(names) if n == "planner"), default=-1)
        done_this_round = set(names[last_planner + 1:])
        plan = result.get("execution_plan")
        planned = list(plan.agents) if plan is not None else []
        pending = [a for a in planned if a not in done_this_round]
        running = pending if pending else ["critic"]

    for name in running:
        steps[name] = AgentStepResponse(agent_name=name, status=AgentStatus.running, duration_ms=0)
    return list(steps.values())


async def _insert_run(run: AgentRunResponse, db: DatabaseProtocol) -> None:
    await db.execute(
        """
        INSERT INTO agent_runs
            (id, query, status, agents_executed, steps, evidence,
             final_report, confidence_score, created_at, owner_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
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
            _run_owner.get(run.id, current_owner()),
        ),
    )


async def _write_run(run: AgentRunResponse, db: DatabaseProtocol) -> None:
    await db.execute(
        """
        UPDATE agent_runs
        SET status = $1, agents_executed = $2, steps = $3, evidence = $4,
            final_report = $5, confidence_score = $6
        WHERE id = $7
        """,
        (
            run.status.value,
            json.dumps(run.agents_executed),
            json.dumps([s.model_dump() for s in run.steps]),
            run.evidence.model_dump_json(),
            run.final_report,
            run.confidence_score,
            run.id,
        ),
    )


async def _insert_report(run: AgentRunResponse, report_fields: dict[str, Any], db: DatabaseProtocol) -> None:
    await db.execute(
        """
        INSERT INTO reports
            (id, query, executive_summary, key_findings, citations,
             confidence_score, created_at, owner_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        (
            run.id,
            run.query,
            report_fields.get("executive_summary", ""),
            json.dumps(report_fields.get("key_findings") or []),
            json.dumps(report_fields.get("citations") or []),
            run.confidence_score,
            run.created_at,
            _run_owner.get(run.id, current_owner()),
        ),
    )


async def _safe_db(coro, run_id: str) -> None:
    # Persistence failure must not abort the research itself.
    try:
        await coro
    except Exception:
        logger.exception("Failed to persist run %s", run_id)


async def _execute_run(run_id: str, state: dict[str, Any], db: DatabaseProtocol) -> None:
    run = _active_runs[run_id]
    result: dict[str, Any] = dict(state)
    try:
        # stream_mode="values" yields the full merged state after every
        # superstep, so progress can be reported as each agent finishes.
        async with asyncio.timeout(settings.max_run_seconds):
            async for snapshot in graph.astream(state, stream_mode="values"):
                result = snapshot
                plan = result.get("execution_plan")
                run = run.model_copy(update={
                    "agents_executed": list(plan.agents) if plan is not None else [],
                    "steps": _progress_steps(result),
                    "evidence": _build_evidence(result),
                    "confidence_score": result.get("confidence_score", 0.0),
                })
                _active_runs[run_id] = run
                await _safe_db(_write_run(run, db), run_id)

        final_report, report_fields = _render_report_markdown(
            result.get("final_report", ""), _unique_warnings(result)
        )
        # A source that failed (a search, a database) is a note in the report, not a failed run.
        # The run only fails when no report came out of it.
        run = run.model_copy(update={
            "steps": _build_steps(result),
            "final_report": final_report,
            "status": AgentStatus.complete if final_report.strip() else AgentStatus.failed,
        })
        _active_runs[run_id] = run
        await _safe_db(_write_run(run, db), run_id)
        if report_fields:
            await _safe_db(_insert_report(run, report_fields, db), run_id)
    except Exception:
        logger.exception("Research workflow failed for run %s", run_id)
        run = run.model_copy(update={
            "status": AgentStatus.failed,
            "steps": [
                s.model_copy(update={"status": AgentStatus.failed}) if s.status == AgentStatus.running else s
                for s in run.steps
            ],
        })
        _active_runs[run_id] = run
        await _safe_db(_write_run(run, db), run_id)


async def start_research(
    query: str,
    db: DatabaseProtocol,
) -> AgentRunResponse:
    """Register the run, launch the graph in the background, and return at once.

    The task is owned by the event loop, not the HTTP request, so the user
    navigating away (or closing the tab) does not cancel it.
    """
    run_id = str(uuid.uuid4())
    state = initial_state(query)

    run = AgentRunResponse(
        id=run_id,
        query=query,
        agents_executed=[],
        steps=[AgentStepResponse(agent_name="planner", status=AgentStatus.running, duration_ms=0)],
        confidence_score=0.0,
        final_report="",
        status=AgentStatus.running,
        created_at=datetime.now(UTC),
    )
    _active_runs[run_id] = run
    _run_owner[run_id] = current_owner()
    await _safe_db(_insert_run(run, db), run_id)

    task = asyncio.create_task(_execute_run(run_id, state, db))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return run


async def fail_orphaned_runs(db: DatabaseProtocol) -> None:
    """Runs left 'running' by a previous process can never finish; mark them failed."""
    try:
        await db.execute("UPDATE agent_runs SET status = 'failed' WHERE status = 'running'")
    except Exception:
        logger.exception("Failed to clean up orphaned runs")

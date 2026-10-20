from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.schemas.common import AgentStatus
from app.schemas.research import AgentRunResponse, AgentStepResponse, RunEvidence
from app.services.postgres_service import DatabaseProtocol
from app.services.request_context import current_owner
from app.services.research_service import get_active_run, list_active_runs


async def list_runs(db: DatabaseProtocol) -> list[AgentRunResponse]:
    rows = await db.fetch_many(
        "SELECT * FROM agent_runs WHERE owner_id = $1 ORDER BY created_at DESC", (current_owner(),)
    )
    runs = {r.id: r for r in (_row_to_run(row) for row in rows)}
    for live in list_active_runs():
        runs[live.id] = live  # in-memory state is fresher than the DB row
    return sorted(runs.values(), key=lambda r: r.created_at, reverse=True)


async def get_run(run_id: str, db: DatabaseProtocol) -> AgentRunResponse | None:
    live = get_active_run(run_id)
    if live is not None:
        return live
    row = await db.fetch_one(
        "SELECT * FROM agent_runs WHERE id = $1 AND owner_id = $2", (run_id, current_owner())
    )
    return _row_to_run(row) if row else None


def _load_json(value: Any, default: Any) -> Any:
    """asyncpg returns JSONB columns as strings; mock rows hold Python objects."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value if value is not None else default


def _row_to_run(row: dict[str, Any]) -> AgentRunResponse:
    steps = [
        AgentStepResponse(
            agent_name=s.get("agent_name", ""),
            status=AgentStatus(s.get("status", "complete")),
            duration_ms=s.get("duration_ms", 0),
            evidence_count=s.get("evidence_count", 0),
        )
        for s in _load_json(row.get("steps"), [])
    ]
    evidence = RunEvidence(**_load_json(row.get("evidence"), {}))
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return AgentRunResponse(
        id=row.get("id", ""),
        query=row.get("query", ""),
        agents_executed=_load_json(row.get("agents_executed"), []),
        steps=steps,
        evidence=evidence,
        confidence_score=row.get("confidence_score", 0.0),
        final_report=row.get("final_report", ""),
        status=AgentStatus(row.get("status", "complete")),
        created_at=created_at or datetime.now(timezone.utc),
    )

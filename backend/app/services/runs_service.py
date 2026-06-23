from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas.common import AgentStatus
from app.schemas.research import AgentRunResponse
from app.services.postgres_service import DatabaseProtocol


async def list_runs(db: DatabaseProtocol) -> list[AgentRunResponse]:
    rows = await db.fetch_many("SELECT * FROM agent_runs")
    return [_row_to_run(row) for row in rows]


async def get_run(run_id: str, db: DatabaseProtocol) -> AgentRunResponse | None:
    row = await db.fetch_one("SELECT * FROM agent_runs WHERE id = $1", (run_id,))
    return _row_to_run(row) if row else None


def _row_to_run(row: dict[str, Any]) -> AgentRunResponse:
    return AgentRunResponse(
        id=row.get("id", ""),
        query=row.get("query", ""),
        agents_executed=[row["agent_name"]] if row.get("agent_name") else [],
        confidence_score=row.get("confidence_score", 0.0),
        final_report=row.get("final_report", ""),
        status=AgentStatus(row.get("status", "complete")),
        created_at=row.get("created_at") or datetime.now(timezone.utc),
    )

import asyncio
import json

import pytest

from app.schemas.agents import ExecutionPlan
from app.schemas.common import AgentStatus
from app.services import research_service
from app.services.postgres_service import SqliteService
from app.services.runs_service import get_run


class _FakeGraph:
    """Yields the same full-state snapshots LangGraph's values stream would."""

    def __init__(self, gate: asyncio.Event) -> None:
        self._gate = gate

    async def astream(self, state, stream_mode="values"):
        state = dict(state)
        state["execution_plan"] = ExecutionPlan(agents=["rag"], reasoning="r")
        state["agent_steps"] = [{"agent_name": "planner", "status": "complete", "duration_ms": 5}]
        yield dict(state)
        await self._gate.wait()
        state["agent_steps"] = state["agent_steps"] + [
            {"agent_name": "rag", "status": "complete", "duration_ms": 7},
            {"agent_name": "critic", "status": "complete", "duration_ms": 3},
            {"agent_name": "report", "status": "complete", "duration_ms": 9},
        ]
        state["confidence_score"] = 0.9
        state["final_report"] = json.dumps({"executive_summary": "done", "key_findings": ["a"], "citations": []})
        yield dict(state)


@pytest.mark.asyncio
async def test_run_starts_immediately_and_finishes_in_background(tmp_path, monkeypatch):
    gate = asyncio.Event()
    monkeypatch.setattr(research_service, "graph", _FakeGraph(gate))
    db = SqliteService(str(tmp_path / "t.db"))

    run = await research_service.start_research("q", db)

    # Returned before the graph finished.
    assert run.status == AgentStatus.running

    await asyncio.sleep(0.05)
    mid = await get_run(run.id, db)
    assert mid.status == AgentStatus.running
    by_name = {s.agent_name: s.status for s in mid.steps}
    assert by_name["planner"] == AgentStatus.complete
    assert by_name["rag"] == AgentStatus.running

    gate.set()
    await asyncio.gather(*research_service._background_tasks)

    done = await get_run(run.id, db)
    assert done.status == AgentStatus.complete
    assert "done" in done.final_report
    # Persisted, not just held in memory.
    row = await db.fetch_one("SELECT status FROM agent_runs WHERE id = $1", (run.id,))
    assert row["status"] == "complete"
    assert await db.fetch_one("SELECT id FROM reports WHERE id = $1", (run.id,))


@pytest.mark.asyncio
async def test_orphaned_running_runs_are_failed_on_startup(tmp_path):
    db = SqliteService(str(tmp_path / "t.db"))
    await db.execute(
        "INSERT INTO agent_runs (id, query, status, agents_executed, steps, evidence, created_at)"
        " VALUES ($1, 'q', 'running', '[]', '[]', '{}', '2025-01-01T00:00:00')",
        ("stale",),
    )
    await research_service.fail_orphaned_runs(db)
    row = await db.fetch_one("SELECT status FROM agent_runs WHERE id = $1", ("stale",))
    assert row["status"] == "failed"

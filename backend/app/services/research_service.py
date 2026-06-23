from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.graph.state import initial_state
from app.graph.workflow import graph
from app.schemas.common import AgentStatus
from app.schemas.research import AgentRunResponse

logger = logging.getLogger(__name__)


async def run_research(query: str, uploaded_files: list[str] | None = None) -> AgentRunResponse:
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
        return AgentRunResponse(
            id=run_id,
            query=query,
            agents_executed=agents_executed,
            confidence_score=result.get("confidence_score", 0.0),
            final_report=result.get("final_report", ""),
            status=status,
            created_at=datetime.now(timezone.utc),
        )
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

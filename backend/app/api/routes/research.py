from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.dependencies import DbDep
from app.config import settings
from app.schemas.research import AgentRunResponse, ResearchRequest
from app.services.llm_service import llm_unavailable_reason
from app.services.research_service import count_running, start_research
from app.tools.sql_tool import check_database
from app.services.runs_service import get_run, list_runs

router = APIRouter(tags=["research"])


@router.post("/query", response_model=AgentRunResponse)
async def submit_query(request: ResearchRequest, db: DbDep) -> AgentRunResponse:
    # Say so up front, in plain words, instead of starting a run that is certain to fail.
    reason = llm_unavailable_reason()
    if reason:
        raise HTTPException(status_code=400, detail=reason)
    # A database the visitor chose but that cannot be reached would otherwise be skipped
    # without a word, and the answer would come from the web alone.
    problem = await check_database()
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    if count_running() >= settings.max_concurrent_runs_per_visitor:
        raise HTTPException(
            status_code=429,
            detail="You already have research running. Wait for it to finish before starting another.",
        )
    return await start_research(request.query, db)


@router.get("/runs", response_model=list[AgentRunResponse])
async def list_all_runs(db: DbDep) -> list[AgentRunResponse]:
    return await list_runs(db)


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run_by_id(run_id: str, db: DbDep) -> AgentRunResponse:
    result = await get_run(run_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result

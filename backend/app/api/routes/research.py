from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.dependencies import DbDep
from app.schemas.research import AgentRunResponse, ResearchRequest
from app.services.research_service import run_research
from app.services.runs_service import get_run, list_runs

router = APIRouter(tags=["research"])


@router.post("/query", response_model=AgentRunResponse)
async def submit_query(request: ResearchRequest) -> AgentRunResponse:
    return await run_research(request.query, request.uploaded_files or None)


@router.get("/runs", response_model=list[AgentRunResponse])
async def list_all_runs(db: DbDep) -> list[AgentRunResponse]:
    return await list_runs(db)


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run_by_id(run_id: str, db: DbDep) -> AgentRunResponse:
    result = await get_run(run_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result

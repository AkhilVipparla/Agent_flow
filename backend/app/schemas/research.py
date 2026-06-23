from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AgentStatus


class ResearchRequest(BaseModel):
    query: str
    uploaded_files: list[str] = []


class AgentStepResponse(BaseModel):
    agent_name: str
    status: AgentStatus
    duration_ms: int
    evidence_count: int


class AgentRunResponse(BaseModel):
    id: str
    query: str
    agents_executed: list[str]
    confidence_score: float
    final_report: str
    status: AgentStatus
    created_at: datetime

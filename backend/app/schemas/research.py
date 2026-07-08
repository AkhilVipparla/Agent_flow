from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.agents import Citation, EvidenceItem
from app.schemas.common import AgentStatus, CamelModel


class ResearchRequest(CamelModel):
    query: str
    uploaded_files: list[str] = []


class AgentStepResponse(CamelModel):
    agent_name: str
    status: AgentStatus
    duration_ms: int
    evidence_count: int = 0


class SearchResultItem(CamelModel):
    title: str
    url: str
    snippet: str


class RunEvidence(CamelModel):
    retrieved_documents: list[EvidenceItem] = Field(default_factory=list)
    sql_results: list[dict[str, Any]] = Field(default_factory=list)
    search_results: list[SearchResultItem] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence_score: float = 0.0


class AgentRunResponse(CamelModel):
    id: str
    query: str
    agents_executed: list[str]
    steps: list[AgentStepResponse] = Field(default_factory=list)
    evidence: RunEvidence = Field(default_factory=RunEvidence)
    confidence_score: float
    final_report: str
    status: AgentStatus
    created_at: datetime

from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    url: str | None = None
    page: int | None = None
    excerpt: str


class ExecutionPlan(BaseModel):
    agents: list[str] = Field(default_factory=list)
    reasoning: str


class EvidenceItem(BaseModel):
    agent: str
    content: str
    citations: list[Citation] = Field(default_factory=list)

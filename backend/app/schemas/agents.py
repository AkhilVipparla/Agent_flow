from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import CamelModel


class Citation(CamelModel):
    source: str
    url: str | None = None
    page: int | None = None
    excerpt: str


class ExecutionPlan(BaseModel):
    agents: list[str] = Field(default_factory=list)
    reasoning: str


class EvidenceItem(CamelModel):
    agent: str
    content: str
    citations: list[Citation] = Field(default_factory=list)

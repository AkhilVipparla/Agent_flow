from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.agents import Citation


class ReportSummary(BaseModel):
    id: str
    query: str
    confidence_score: float
    created_at: datetime


class ReportResponse(BaseModel):
    id: str
    query: str
    executive_summary: str
    key_findings: list[str]
    citations: list[Citation]
    confidence_score: float
    created_at: datetime


class ReportListResponse(BaseModel):
    reports: list[ReportSummary]
    total: int

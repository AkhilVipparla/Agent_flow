from __future__ import annotations

from datetime import datetime

from app.schemas.agents import Citation
from app.schemas.common import CamelModel


class ReportSummary(CamelModel):
    id: str
    query: str
    confidence_score: float
    created_at: datetime


class ReportResponse(CamelModel):
    id: str
    query: str
    executive_summary: str
    key_findings: list[str]
    citations: list[Citation]
    confidence_score: float
    created_at: datetime


class ReportListResponse(CamelModel):
    reports: list[ReportSummary]
    total: int

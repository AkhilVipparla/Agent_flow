from __future__ import annotations

from app.schemas.agents import Citation
from pydantic import BaseModel, Field, field_validator


class LLMReportContent(BaseModel):
    """Structured output returned by the LLM synthesis step in ReportAgent."""

    executive_summary: str = Field(
        description="A concise executive summary synthesising all evidence collected."
    )
    key_findings: list[str] = Field(
        description="Ordered list of specific, evidence-backed findings. Each item is one sentence."
    )


class ReportOutput(BaseModel):
    """Full assembled report written to AgentState.final_report as JSON."""

    executive_summary: str
    key_findings: list[str]
    citations: list[Citation]
    confidence_score: float = Field(ge=0.0, le=1.0)

    @field_validator("confidence_score", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CriticOutput(BaseModel):
    """Structured output returned by the LLM evaluation step in CriticAgent."""

    decision: Literal["PASS", "RETRY"]
    confidence: float = Field(
        description="Confidence in the collected evidence, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )
    reason: str = Field(
        description="One sentence explaining why the decision was made."
    )
    missing_information: list[str] = Field(
        description="Specific information gaps the Planner should address on retry. Empty on PASS.",
        default_factory=list,
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

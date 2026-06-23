from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.agents import Citation


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class LLMSearchAnalysis(BaseModel):
    """Structured output target for the LLM analysis step."""
    findings: list[str] = Field(
        description="One concise sentence per useful source summarising its contribution to the query.",
        default_factory=list,
    )
    confidence: float = Field(
        description="Overall confidence in the retrieved information, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class SearchOutput(BaseModel):
    """Shape written into state['search_results'] as a single dict entry."""
    findings: list[str] = Field(default_factory=list)
    sources: list[WebSearchResult] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

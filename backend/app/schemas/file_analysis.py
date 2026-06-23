from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, Field, field_validator

from app.schemas.agents import Citation


class PDFPage(TypedDict):
    page: int
    text: str


class SheetData(TypedDict):
    sheet: str
    headers: list[str]
    rows: list[dict[str, Any]]


class TableSummary(BaseModel):
    name: str = Field(description="Sheet name or 'Page N' identifying the source table.")
    summary: str = Field(description="One to two sentences summarising the table's business content.")


class LLMFileAnalysis(BaseModel):
    """Structured output returned by the LLM analysis step in FileAnalysisAgent."""

    findings: list[str] = Field(
        description="Specific, evidence-backed business findings extracted from the files. Each item is one sentence.",
        default_factory=list,
    )
    table_summaries: list[TableSummary] = Field(
        description="One summary per table or structured dataset found in the files.",
        default_factory=list,
    )
    confidence: float = Field(
        description="Confidence in the extracted information, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class FileAnalysisOutput(BaseModel):
    """Full structured output written to AgentState.file_results as a dict entry."""

    findings: list[str] = Field(default_factory=list)
    tables: list[TableSummary] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

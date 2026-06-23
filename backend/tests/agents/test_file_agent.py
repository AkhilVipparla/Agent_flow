from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.file_agent import FileAnalysisAgent
from app.graph.state import initial_state
from app.schemas.file_analysis import LLMFileAnalysis, TableSummary

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FINDINGS = [
    "Q4 revenue reached $142M, up 23% year-over-year.",
    "Operating margin improved to 18.4% from 15.1% in Q3.",
]
_TABLE_SUMMARIES = [
    TableSummary(name="Sheet1", summary="Quarterly revenue breakdown across four business segments."),
]
_PDF_PAGES = [{"page": 1, "text": "Revenue grew 23% in Q4 to reach $142M."}]
_EXCEL_SHEETS = [
    {"sheet": "Sheet1", "headers": ["Quarter", "Revenue"], "rows": [{"Quarter": "Q4", "Revenue": "142M"}]}
]


def _make_agent(llm_output: LLMFileAnalysis) -> FileAnalysisAgent:
    mock_llm = MagicMock()
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=llm_output)
    mock_llm.with_structured_output = MagicMock(return_value=structured_llm)

    with patch("app.agents.base_agent.get_llm", return_value=mock_llm):
        agent = FileAnalysisAgent()

    return agent


def _llm_output(confidence: float = 0.85) -> LLMFileAnalysis:
    return LLMFileAnalysis(
        findings=_FINDINGS,
        table_summaries=_TABLE_SUMMARIES,
        confidence=confidence,
    )


def _state_with_files(file_paths: list[str]) -> dict:
    state = initial_state("What were the Q4 revenue results?")
    state["uploaded_files"] = file_paths
    return state


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_file_results_set_on_valid_files():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["report.pdf"]))

    assert "file_results" in result
    assert len(result["file_results"]) == 1


@pytest.mark.asyncio
async def test_findings_from_llm_in_state():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["report.pdf"]))

    stored = result["file_results"][0]
    assert stored["findings"] == _FINDINGS


@pytest.mark.asyncio
async def test_tables_from_llm_in_state():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["report.pdf"]))

    stored = result["file_results"][0]
    assert len(stored["tables"]) == 1
    assert stored["tables"][0]["name"] == "Sheet1"


@pytest.mark.asyncio
async def test_citations_reference_source_files():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["annual_report.pdf"]))

    stored = result["file_results"][0]
    assert any(c["source"] == "annual_report.pdf" for c in stored["citations"])


@pytest.mark.asyncio
async def test_citations_appended_to_state():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["report.pdf"]))

    assert "citations" in result
    assert len(result["citations"]) == 1
    assert result["citations"][0].source == "report.pdf"


@pytest.mark.asyncio
async def test_confidence_from_llm():
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output(confidence=0.78))
        result = await agent.run(_state_with_files(["report.pdf"]))

    stored = result["file_results"][0]
    assert stored["confidence"] == pytest.approx(0.78)


@pytest.mark.asyncio
async def test_empty_uploaded_files_returns_no_update():
    agent = _make_agent(_llm_output())
    result = await agent.run(_state_with_files([]))

    assert result == {}


@pytest.mark.asyncio
async def test_pdf_tool_called_for_pdf_file():
    with (
        patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES) as mock_pdf,
        patch("app.agents.file_agent.parse_excel", new_callable=AsyncMock) as mock_excel,
    ):
        agent = _make_agent(_llm_output())
        await agent.run(_state_with_files(["report.pdf"]))

    mock_pdf.assert_called_once_with("report.pdf")
    mock_excel.assert_not_called()


@pytest.mark.asyncio
async def test_excel_tool_called_for_xlsx_file():
    with (
        patch("app.agents.file_agent.parse_excel", new_callable=AsyncMock, return_value=_EXCEL_SHEETS) as mock_excel,
        patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock) as mock_pdf,
    ):
        agent = _make_agent(_llm_output())
        await agent.run(_state_with_files(["data.xlsx"]))

    mock_excel.assert_called_once_with("data.xlsx")
    mock_pdf.assert_not_called()


@pytest.mark.asyncio
async def test_content_key_present_for_critic_compatibility():
    """file_results dicts must have a 'content' key for CriticAgent._summarise_rag."""
    with patch("app.agents.file_agent.parse_pdf", new_callable=AsyncMock, return_value=_PDF_PAGES):
        agent = _make_agent(_llm_output())
        result = await agent.run(_state_with_files(["report.pdf"]))

    stored = result["file_results"][0]
    assert "content" in stored
    assert stored["content"] != ""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, append_citations, append_file_results
from app.schemas.agents import Citation
from app.schemas.file_analysis import FileAnalysisOutput, LLMFileAnalysis
from app.tools.excel_parser_tool import parse_excel
from app.tools.pdf_parser_tool import parse_pdf

logger = logging.getLogger(__name__)

_EXCEL_EXTENSIONS = {".xlsx", ".xls", ".csv"}
_PAGE_CHAR_LIMIT = 600
_ROW_DISPLAY_LIMIT = 10

_SYSTEM_PROMPT = """\
You are a document analyst extracting business intelligence from enterprise files.

Given parsed content from PDFs and spreadsheets, your tasks:
1. Extract specific, evidence-backed business findings — facts, numbers, dates, and trends.
2. For each table or structured dataset, write a 1-2 sentence summary of its business content.
3. Score your confidence in the extracted information from 0.0 to 1.0.

Rules:
- Only use information present in the provided content. Do not invent or infer beyond what is stated.
- Be specific: include numbers, percentages, names, and values wherever possible.
- Skip pages or sheets with no meaningful business content.
- Return only structured JSON matching the required schema.
"""

_USER_PROMPT = """\
Research Query: {query}

--- Parsed File Content ---

{formatted_content}

Extract findings and summarize tables from the content above.
"""


def _format_pdf_pages(filename: str, pages: list[dict]) -> str:
    parts = []
    for p in pages:
        text = p["text"][:_PAGE_CHAR_LIMIT]
        if text:
            parts.append(f"[PDF: {filename}, Page {p['page']}]\n{text}")
    return "\n\n".join(parts)


def _format_sheets(filename: str, sheets: list[dict]) -> str:
    parts = []
    for s in sheets:
        headers = ", ".join(s["headers"])
        row_lines = "\n".join(
            ", ".join(f"{k}: {v}" for k, v in row.items())
            for row in s["rows"][:_ROW_DISPLAY_LIMIT]
        )
        parts.append(f"[{Path(filename).suffix[1:].upper()}: {filename}, Sheet: {s['sheet']}]\nHeaders: {headers}\n{row_lines}")
    return "\n\n".join(parts)


class FileAnalysisAgent(BaseAgent):
    name = "file"

    def __init__(self) -> None:
        super().__init__()
        self._structured_llm = self._llm.with_structured_output(LLMFileAnalysis)

    async def run(self, state: AgentState) -> dict[str, Any]:
        uploaded_files: list[str] = state.get("uploaded_files", [])  # type: ignore[call-overload]
        if not uploaded_files:
            logger.info("FileAnalysisAgent: no uploaded files in state — skipping")
            return {}

        parsed_sections: list[str] = []
        source_names: list[str] = []

        for file_path in uploaded_files:
            path = Path(file_path)
            ext = path.suffix.lower()
            try:
                if ext == ".pdf":
                    pages = await parse_pdf(file_path)
                    section = _format_pdf_pages(path.name, pages)
                elif ext in _EXCEL_EXTENSIONS:
                    sheets = await parse_excel(file_path)
                    section = _format_sheets(path.name, sheets)
                else:
                    logger.warning("FileAnalysisAgent: unsupported extension %r — skipping %r", ext, file_path)
                    continue

                if section:
                    parsed_sections.append(section)
                    source_names.append(path.name)

            except (FileNotFoundError, ValueError) as exc:
                logger.warning("FileAnalysisAgent: failed to parse %r: %s", file_path, exc)

        if not parsed_sections:
            logger.warning("FileAnalysisAgent: no content extracted from any uploaded file")
            return {}

        messages = [
            ("system", _SYSTEM_PROMPT),
            (
                "human",
                _USER_PROMPT.format(
                    query=state["query"],
                    formatted_content="\n\n".join(parsed_sections),
                ),
            ),
        ]

        analysis: LLMFileAnalysis = await self._structured_llm.ainvoke(messages)

        first_finding = analysis.findings[0][:200] if analysis.findings else ""
        citations = [
            Citation(source=name, url=None, page=None, excerpt=first_finding)
            for name in source_names
        ]

        output = FileAnalysisOutput(
            findings=analysis.findings,
            tables=analysis.table_summaries,
            citations=citations,
            confidence=analysis.confidence,
        )

        output_dict = output.model_dump()
        output_dict["content"] = "\n".join(output.findings)

        return {
            **append_file_results([output_dict]),
            **append_citations(citations),
        }

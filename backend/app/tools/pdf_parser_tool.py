from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pypdf

from app.schemas.file_analysis import PDFPage

logger = logging.getLogger(__name__)


def _read_pdf_sync(file_path: str) -> list[PDFPage]:
    try:
        reader = pypdf.PdfReader(file_path)
        pages: list[PDFPage] = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text.strip()})
    except (pypdf.errors.PyPdfError, ValueError, OSError, KeyError, TypeError) as exc:
        # A corrupt, truncated, encrypted or renamed file is a bad upload (HTTP 400), not a server fault.
        logger.info("parse_pdf: unreadable PDF (%s)", type(exc).__name__)
        raise ValueError("This file could not be read as a PDF. It may be corrupt, encrypted, or not a PDF.") from exc
    return pages


async def parse_pdf(file_path: str) -> list[PDFPage]:
    """Extract text page-by-page from a PDF file.

    Returns a list of dicts with 'page' (1-indexed) and 'text' keys.
    Raises FileNotFoundError for missing files, ValueError for non-PDF input.
    """
    path = Path(file_path)
    if not await asyncio.to_thread(path.exists):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix!r}")

    loop = asyncio.get_event_loop()
    pages = await loop.run_in_executor(None, _read_pdf_sync, str(path))
    logger.debug("parse_pdf: extracted %d pages from %r", len(pages), path.name)
    return pages

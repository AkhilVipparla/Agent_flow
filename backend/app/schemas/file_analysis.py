from __future__ import annotations

from typing import Any, TypedDict


class PDFPage(TypedDict):
    page: int
    text: str


class SheetData(TypedDict):
    sheet: str
    headers: list[str]
    rows: list[dict[str, Any]]

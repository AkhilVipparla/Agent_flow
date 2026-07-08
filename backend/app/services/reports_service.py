from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.schemas.reports import ReportListResponse, ReportResponse, ReportSummary
from app.services.postgres_service import DatabaseProtocol


async def list_reports(db: DatabaseProtocol) -> ReportListResponse:
    rows = await db.fetch_many("SELECT * FROM reports ORDER BY created_at DESC")
    summaries = [_row_to_summary(row) for row in rows]
    return ReportListResponse(reports=summaries, total=len(summaries))


async def delete_report(report_id: str, db: DatabaseProtocol) -> None:
    await db.execute("DELETE FROM reports WHERE id = $1", (report_id,))


def _load_json(value: Any, default: Any) -> Any:
    """asyncpg returns JSONB columns as strings; mock rows hold Python objects."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value if value is not None else default


async def get_report(report_id: str, db: DatabaseProtocol) -> ReportResponse | None:
    row = await db.fetch_one("SELECT * FROM reports WHERE id = $1", (report_id,))
    return _row_to_report(row) if row else None


def _row_to_summary(row: dict[str, Any]) -> ReportSummary:
    return ReportSummary(
        id=row.get("id", ""),
        query=row.get("query", ""),
        confidence_score=row.get("confidence_score", 0.0),
        created_at=_parse_dt(row.get("created_at")),
    )


def _row_to_report(row: dict[str, Any]) -> ReportResponse:
    return ReportResponse(
        id=row.get("id", ""),
        query=row.get("query", ""),
        executive_summary=row.get("executive_summary", ""),
        key_findings=_load_json(row.get("key_findings"), []),
        citations=_load_json(row.get("citations"), []),
        confidence_score=row.get("confidence_score", 0.0),
        created_at=_parse_dt(row.get("created_at")),
    )


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)

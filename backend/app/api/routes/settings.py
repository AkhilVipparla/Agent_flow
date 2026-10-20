from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from app.services.request_context import customer_db_url, llm_credentials, use_demo_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["settings"])

_PREVIEW_ROWS = 5
_MAX_TABLES = 20
_MAX_CELL_CHARS = 80
_DEMO_CACHE_TTL = 60.0
_demo_cache: tuple[float, dict[str, Any]] | None = None


@router.post("/settings/test")
async def test_settings() -> dict:
    """Check the visitor's credentials (sent as headers) without running research."""
    result: dict = {"llm": {"configured": False}, "database": {"configured": False}}

    creds = llm_credentials.get()
    if creds is not None:
        result["llm"] = {"configured": True, "ok": False}
        try:
            from app.services.llm_service import get_llm
            await get_llm().ainvoke("Reply with the single word: ok")
            result["llm"]["ok"] = True
        except Exception as exc:
            logger.warning("Settings test: LLM check failed (%s)", type(exc).__name__)
            result["llm"]["error"] = _safe_error(exc, [creds.api_key])

    db_url = customer_db_url.get()
    if db_url or use_demo_db.get():
        result["database"] = {"configured": True, "ok": False, "demo": not db_url}
        try:
            from app.tools.sql_tool import get_schema_description
            schema = await get_schema_description(force_refresh=True)
            result["database"]["ok"] = True
            result["database"]["tables"] = sum(1 for line in schema.splitlines() if line.startswith("  "))
        except Exception as exc:
            logger.warning("Settings test: database check failed (%s)", type(exc).__name__)
            result["database"]["error"] = _safe_error(exc, [db_url or ""])
    return result


@router.get("/settings/demo")
async def demo_database() -> dict:
    """Describe the shared demo database: its tables, columns, row counts and a few rows."""
    from app.tools.sql_tool import get_demo_service

    global _demo_cache
    db = get_demo_service()
    if db is None:
        return {"available": False, "tables": []}

    now = time.monotonic()
    if _demo_cache and now - _demo_cache[0] < _DEMO_CACHE_TTL:
        return _demo_cache[1]

    try:
        from app.tools.sql_tool import _PG_COLUMNS_SQL
        columns = await db.fetch_many(_PG_COLUMNS_SQL, limit=10000)
        by_table: dict[str, list[dict[str, str]]] = {}
        for c in columns:
            by_table.setdefault(c["table_name"], []).append({"name": c["column_name"], "type": c["data_type"]})

        tables = []
        for name, cols in list(by_table.items())[:_MAX_TABLES]:
            # Table names come from information_schema, never from the visitor; still quoted.
            quoted = '"' + name.replace('"', '""') + '"'
            count_row = await db.fetch_one(f"SELECT COUNT(*) AS n FROM {quoted}")
            rows = await db.fetch_many(f"SELECT * FROM {quoted} LIMIT {_PREVIEW_ROWS}", limit=_PREVIEW_ROWS)
            tables.append({
                "name": name,
                "columns": cols,
                "rowCount": (count_row or {}).get("n", 0),
                "sampleRows": [_trim_row(r) for r in rows],
            })
        payload = {"available": True, "tables": tables}
    except Exception as exc:
        logger.warning("Demo database preview failed (%s)", type(exc).__name__)
        return {"available": False, "tables": [], "error": "The demo database could not be read."}

    _demo_cache = (now, payload)
    return payload


def _trim_row(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in jsonable_encoder(row).items():
        if isinstance(value, str) and len(value) > _MAX_CELL_CHARS:
            value = value[:_MAX_CELL_CHARS] + "..."
        elif isinstance(value, (dict, list)):
            value = str(value)[:_MAX_CELL_CHARS]
        out[key] = value
    return out


def _safe_error(exc: Exception, secrets: list[str]) -> str:
    """Short failure reason that never echoes a secret back to the browser."""
    text = f"{type(exc).__name__}: {exc}"
    for secret in secrets:
        if len(secret) > 3:
            text = text.replace(secret, "***")
    return text[:300]

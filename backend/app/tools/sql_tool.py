from __future__ import annotations

import re
from typing import Any

from app.services.postgres_service import DatabaseProtocol, get_database_service

# ---------------------------------------------------------------------------
# Safety constants
# ---------------------------------------------------------------------------

_ALLOWED_FIRST_TOKEN = "SELECT"

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bINSERT\b",   re.IGNORECASE),
    re.compile(r"\bUPDATE\b",   re.IGNORECASE),
    re.compile(r"\bDELETE\b",   re.IGNORECASE),
    re.compile(r"\bDROP\b",     re.IGNORECASE),
    re.compile(r"\bALTER\b",    re.IGNORECASE),
    re.compile(r"\bCREATE\b",   re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bEXEC\b",     re.IGNORECASE),
    re.compile(r"\bEXECUTE\b",  re.IGNORECASE),
    re.compile(r"\bGRANT\b",    re.IGNORECASE),
    re.compile(r"\bREVOKE\b",   re.IGNORECASE),
    re.compile(r"--"),           # inline comment (SQL injection vector)
    re.compile(r"/\*"),          # block comment
]

_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)
_DEFAULT_LIMIT = 100


class SQLValidationError(ValueError):
    """Raised when a query fails safety checks before execution."""


class SQLExecutionError(RuntimeError):
    """Raised when a query fails at execution time; never leaks DB internals."""


def _validate(sql: str) -> str:
    """Validate and normalise SQL. Returns the (possibly modified) query string."""
    stripped = sql.strip().rstrip(";")

    first_token = stripped.split()[0].upper() if stripped.split() else ""
    if first_token != _ALLOWED_FIRST_TOKEN:
        raise SQLValidationError(
            f"Only SELECT statements are permitted. Received first token: {first_token!r}"
        )

    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(stripped):
            raise SQLValidationError(
                f"Query contains a disallowed keyword or pattern: {pattern.pattern!r}"
            )

    # Reject stacked queries (multiple statements)
    if ";" in stripped:
        raise SQLValidationError("Stacked queries (multiple statements) are not permitted.")

    # Enforce row cap
    if not _LIMIT_RE.search(stripped):
        stripped = f"{stripped} LIMIT {_DEFAULT_LIMIT}"

    return stripped


_service: DatabaseProtocol | None = None


def _get_service() -> DatabaseProtocol:
    global _service
    if _service is None:
        _service = get_database_service()
    return _service


async def execute_sql(
    sql: str,
    params: tuple[Any, ...] | None = None,
) -> list[dict[str, Any]]:
    """Validate and execute a SQL query. Returns rows as a list of dicts.

    Raises SQLValidationError before touching the DB if the query is unsafe.
    Raises SQLExecutionError on DB failure without leaking internal error text.
    """
    safe_sql = _validate(sql)
    try:
        return await _get_service().fetch_many(safe_sql, params=params)
    except (SQLValidationError, SQLExecutionError):
        raise
    except Exception:
        raise SQLExecutionError("Query execution failed. The query may reference a non-existent table or column.")

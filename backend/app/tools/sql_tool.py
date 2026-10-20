from __future__ import annotations

import re
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit

from app.services.net_guard import HostNotAllowedError, assert_public_host
from app.services.postgres_service import DatabaseProtocol, PostgresService, get_database_service
from app.services.request_context import customer_db_url, use_demo_db

# ---------------------------------------------------------------------------
# Safety constants
# ---------------------------------------------------------------------------

_ALLOWED_FIRST_KEYWORD = "SELECT"

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
    if first_token != _ALLOWED_FIRST_KEYWORD:
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


class CustomerDatabaseError(ValueError):
    """The visitor-supplied database URL is missing, malformed, or not allowed."""


def validate_customer_db_url(url: str) -> str:
    """Accept only postgres URLs whose host is not an internal address (SSRF guard)."""
    parts = urlsplit(url)
    if parts.scheme not in ("postgresql", "postgres", "postgresql+asyncpg"):
        raise CustomerDatabaseError("Only PostgreSQL databases are supported.")
    try:
        assert_public_host(parts.hostname, parts.port or 5432)
    except HostNotAllowedError as exc:
        raise CustomerDatabaseError(f"Database {str(exc).lower()}") from None
    return url


_customer_services: dict[str, DatabaseProtocol] = {}


@lru_cache(maxsize=8)
def _customer_service(url: str) -> DatabaseProtocol:
    # Small pools and a read-only session: this is someone else's database.
    service = PostgresService(url, read_only=True, min_size=1, max_size=3)
    _customer_services[url] = service
    return service


def _customer_service_cache_values() -> list[DatabaseProtocol]:
    return list(_customer_services.values())


async def close_customer_pools() -> None:
    """Close every cached user/demo database pool (called on shutdown)."""
    services = _customer_service_cache_values()
    _customer_service.cache_clear()
    _customer_services.clear()
    for service in services:
        await service.close()


def get_demo_service() -> DatabaseProtocol | None:
    """The operator-configured read-only demo database, or None when not configured."""
    from app.config import settings

    # The URL comes from server config, not a visitor, so the SSRF guard doesn't apply.
    return _customer_service(settings.demo_database_url) if settings.demo_database_url else None


def _get_service() -> DatabaseProtocol:
    """The database the SQL agent should read for this request.

    Priority: the visitor's own database, then the shared demo database if they
    chose it in Settings, then (local development only) the app's own database.
    """
    from app.config import settings

    global _service
    url = customer_db_url.get()
    if url:
        return _customer_service(validate_customer_db_url(url))
    if use_demo_db.get():
        demo = get_demo_service()
        if demo is None:
            raise CustomerDatabaseError("The demo database is not available on this server.")
        return demo
    if settings.require_customer_db:
        raise CustomerDatabaseError("Add your database connection in Settings to use SQL analysis.")
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
        raise SQLExecutionError("Query execution failed. The query may reference a non-existent table or column.") from None


# ---------------------------------------------------------------------------
# Schema discovery — lets the agent work against any customer database.
# ---------------------------------------------------------------------------

_SCHEMA_TTL_SECONDS = 60
_schema_cache: dict[str, tuple[float, str]] = {}

_PG_COLUMNS_SQL = """
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position
"""

_PG_FKS_SQL = """
SELECT kcu.table_name, kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
"""


async def _introspect_postgres(db: DatabaseProtocol) -> str:
    columns = await db.fetch_many(_PG_COLUMNS_SQL, limit=10000)
    fks = await db.fetch_many(_PG_FKS_SQL, limit=10000)
    tables: dict[str, list[str]] = {}
    for c in columns:
        tables.setdefault(c["table_name"], []).append(f'{c["column_name"]} {c["data_type"]}')
    lines = [f"  {t} ({', '.join(cols)})" for t, cols in tables.items()]
    out = "Tables available:\n" + "\n".join(lines)
    if fks:
        rels = "; ".join(
            f'{f["table_name"]}.{f["column_name"]} -> {f["ref_table"]}.{f["ref_column"]}' for f in fks
        )
        out += f"\n\nRelationships: {rels}"
    return out


async def _introspect_sqlite(db: DatabaseProtocol) -> str:
    names = await db.fetch_many(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        limit=10000,
    )
    lines = []
    for n in names:
        cols = await db.fetch_many("SELECT name, type FROM pragma_table_info($1)", (n["name"],), limit=10000)
        lines.append(f"  {n['name']} ({', '.join(c['name'] + ' ' + (c['type'] or '') for c in cols)})")
    return "Tables available:\n" + "\n".join(lines)


async def get_schema_description(force_refresh: bool = False) -> str:
    """Describe the live database schema (tables, columns, foreign keys) for LLM prompts.

    Cached briefly per database so a burst of questions doesn't re-query
    information_schema.
    """
    import time

    db = _get_service()
    key = str(id(db))
    now = time.monotonic()
    cached = _schema_cache.get(key)
    if not force_refresh and cached and now - cached[0] < _SCHEMA_TTL_SECONDS:
        return cached[1]
    from app.services.postgres_service import SqliteService

    text = await (_introspect_sqlite(db) if isinstance(db, SqliteService) else _introspect_postgres(db))
    if len(_schema_cache) > 32:
        _schema_cache.clear()
    _schema_cache[key] = (now, text)
    return text

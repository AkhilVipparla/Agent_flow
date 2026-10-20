from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import sqlite3
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class DatabaseProtocol(Protocol):
    async def fetch_many(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    async def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None: ...

    async def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> None: ...

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# Mock — returns realistic rows without a running PostgreSQL instance.
# ---------------------------------------------------------------------------

_MOCK_AGENT_RUNS: list[dict[str, Any]] = [
    {
        "id": "run-001",
        "query": "Q4 revenue breakdown",
        "status": "complete",
        "agents_executed": ["planner", "rag", "sql", "critic", "report"],
        "steps": [
            {"agent_name": "planner", "status": "complete", "duration_ms": 820, "evidence_count": 0},
            {"agent_name": "rag", "status": "complete", "duration_ms": 1760, "evidence_count": 5},
            {"agent_name": "sql", "status": "complete", "duration_ms": 1430, "evidence_count": 3},
            {"agent_name": "critic", "status": "complete", "duration_ms": 560, "evidence_count": 0},
            {"agent_name": "report", "status": "complete", "duration_ms": 1180, "evidence_count": 0},
        ],
        "evidence": {
            "retrieved_documents": [],
            "sql_results": [],
            "search_results": [],
            "citations": [],
            "confidence_score": 0.91,
        },
        "final_report": "## Executive Summary\n\nQ4 revenue reached $142M, up 23% year-over-year.",
        "confidence_score": 0.91,
        "created_at": "2025-01-15T10:23:00Z",
    },
    {
        "id": "run-002",
        "query": "Customer churn analysis",
        "status": "complete",
        "agents_executed": ["planner", "rag", "search", "critic", "report"],
        "steps": [
            {"agent_name": "planner", "status": "complete", "duration_ms": 910, "evidence_count": 0},
            {"agent_name": "rag", "status": "complete", "duration_ms": 2100, "evidence_count": 4},
            {"agent_name": "search", "status": "complete", "duration_ms": 2400, "evidence_count": 4},
            {"agent_name": "critic", "status": "complete", "duration_ms": 490, "evidence_count": 0},
            {"agent_name": "report", "status": "complete", "duration_ms": 1320, "evidence_count": 0},
        ],
        "evidence": {
            "retrieved_documents": [],
            "sql_results": [],
            "search_results": [],
            "citations": [],
            "confidence_score": 0.85,
        },
        "final_report": "## Executive Summary\n\nChurn decreased to 4.2% annually, concentrated in SMB accounts.",
        "confidence_score": 0.85,
        "created_at": "2025-01-18T14:05:00Z",
    },
]

_MOCK_DOCUMENTS: list[dict[str, Any]] = [
    {"id": "doc-001", "filename": "Q4_2024_Financial_Report.pdf", "file_type": "pdf", "chunk_count": 48, "created_at": "2025-01-10T08:00:00Z"},
    {"id": "doc-002", "filename": "Customer_Churn_H2_2024.pdf", "file_type": "pdf", "chunk_count": 31, "created_at": "2025-01-12T11:30:00Z"},
    {"id": "doc-003", "filename": "AWS_Cost_Explorer_Jan2025.csv", "file_type": "csv", "chunk_count": 214, "created_at": "2025-01-14T09:15:00Z"},
]

_MOCK_USAGE: list[dict[str, Any]] = [
    {"org_id": "org-001", "org_name": "Acme Corp",     "tokens_used": 142000, "cost_usd": 1.42, "report_count": 34},
    {"org_id": "org-002", "org_name": "Globex Inc",    "tokens_used": 98500,  "cost_usd": 0.99, "report_count": 21},
    {"org_id": "org-003", "org_name": "Initech Ltd",   "tokens_used": 211300, "cost_usd": 2.11, "report_count": 58},
    {"org_id": "org-004", "org_name": "Umbrella Corp", "tokens_used": 67800,  "cost_usd": 0.68, "report_count": 15},
]

_MOCK_REPORTS: list[dict[str, Any]] = [
    {
        "id": "rep-001",
        "query": "Q4 revenue breakdown",
        "executive_summary": "Q4 revenue reached $142M, a 23% year-over-year increase driven by SaaS subscription growth.",
        "key_findings": [
            "Revenue reached $142M (+23% YoY).",
            "Gross margin improved to 68%.",
            "Operating income was $53M.",
        ],
        "citations": [
            {"source": "Q4 2024 Earnings Report", "url": None, "page": 4, "excerpt": "Revenue reached $142M, a 23% year-over-year increase."},
        ],
        "confidence_score": 0.91,
        "created_at": "2025-01-15T10:23:00Z",
    },
    {
        "id": "rep-002",
        "query": "Customer churn analysis",
        "executive_summary": "Annual churn decreased to 4.2%, with NPS rising to 72 on the back of reliability and support improvements.",
        "key_findings": [
            "Churn rate decreased to 4.2% annually.",
            "Net Promoter Score rose to 72, up from 61 in 2023.",
        ],
        "citations": [
            {"source": "Customer Satisfaction Survey 2024", "url": None, "page": 1, "excerpt": "Churn rate decreased to 4.2% annually."},
        ],
        "confidence_score": 0.85,
        "created_at": "2025-01-18T14:05:00Z",
    },
    {
        "id": "rep-003",
        "query": "Infrastructure cost optimisation",
        "executive_summary": "The Kubernetes migration reduced infrastructure costs by 31% while maintaining 99.97% uptime.",
        "key_findings": [
            "Infrastructure costs down 31% after Kubernetes migration.",
            "Platform processed 1.4 billion API calls in Q4 2024 with 99.97% uptime.",
        ],
        "citations": [
            {"source": "Engineering Infrastructure Report Q4 2024", "url": None, "page": 3, "excerpt": "The migration to Kubernetes reduced infrastructure costs by 31%."},
        ],
        "confidence_score": 0.72,
        "created_at": "2025-01-20T09:47:00Z",
    },
]


class MockDatabaseService:
    """Returns pre-seeded rows; no database connection required."""

    async def fetch_many(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        sql_lower = sql.lower()
        if "agent_runs" in sql_lower or "agentrun" in sql_lower:
            return _MOCK_AGENT_RUNS[:limit]
        if "documents" in sql_lower:
            return _MOCK_DOCUMENTS[:limit]
        if "usage" in sql_lower:
            return _MOCK_USAGE[:limit]
        if "report" in sql_lower:
            return _MOCK_REPORTS[:limit]
        # Default: mixed summary view
        return [
            {"metric": "total_reports",    "value": 127},
            {"metric": "total_agent_runs", "value": 634},
            {"metric": "avg_confidence",   "value": 0.84},
            {"metric": "total_tokens",     "value": 519600},
            {"metric": "total_cost_usd",   "value": 5.20},
        ][:limit]

    async def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        rows = await self.fetch_many(sql, params, limit=100)
        # Lookups by id pass the id as the first parameter — honour it so
        # "not found" paths behave like the real database.
        if params and rows and "id" in rows[0]:
            for row in rows:
                if row.get("id") == params[0]:
                    return row
            return None
        return rows[0] if rows else None

    async def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> None:
        logger.info("MockDatabaseService.execute (no-op): %s", sql.split()[0] if sql else "")

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Local — SQLite file on disk; real persistence with no external services.
# ---------------------------------------------------------------------------

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    owner_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS document_files (
    document_id TEXT PRIMARY KEY REFERENCES documents (id) ON DELETE CASCADE,
    content BLOB NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'application/pdf',
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    agents_executed TEXT NOT NULL,
    steps TEXT NOT NULL,
    evidence TEXT NOT NULL,
    final_report TEXT,
    confidence_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    owner_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS app_users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES app_users (id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    executive_summary TEXT,
    key_findings TEXT,
    citations TEXT,
    confidence_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    owner_id TEXT NOT NULL DEFAULT ''
);
"""

_PLACEHOLDER_RE = re.compile(r"\$\d+")


def _to_sqlite_sql(sql: str) -> str:
    """asyncpg-style $1, $2... placeholders -> sqlite's ?."""
    return _PLACEHOLDER_RE.sub("?", sql)


def _adapt_params(params: tuple[Any, ...] | None) -> tuple[Any, ...]:
    if not params:
        return ()
    return tuple(p.isoformat() if isinstance(p, datetime) else p for p in params)


class SqliteService:
    """Real persistence to a local .db file — no Docker/Postgres required.

    Each call opens a short-lived connection on a worker thread; fine for a
    single-user dev app and avoids cross-thread sqlite3 connection issues.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.executescript(_SQLITE_SCHEMA)
            for table in ("documents", "agent_runs", "reports"):
                # Databases created before per-visitor ownership lack the column.
                with contextlib.suppress(sqlite3.OperationalError):
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN owner_id TEXT NOT NULL DEFAULT ''")  # noqa: S608
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def fetch_many(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            conn = self._connect()
            try:
                cur = conn.execute(_to_sqlite_sql(sql), _adapt_params(params))
                return [dict(row) for row in cur.fetchmany(limit)]
            finally:
                conn.close()

        return await asyncio.to_thread(_run)

    async def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        def _run() -> dict[str, Any] | None:
            conn = self._connect()
            try:
                cur = conn.execute(_to_sqlite_sql(sql), _adapt_params(params))
                row = cur.fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

        return await asyncio.to_thread(_run)

    async def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> None:
        def _run() -> None:
            conn = self._connect()
            try:
                conn.execute(_to_sqlite_sql(sql), _adapt_params(params))
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_run)

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Real — asyncpg connection pool; lazy init.
# ---------------------------------------------------------------------------

class PostgresService:
    """Real PostgreSQL service using asyncpg connection pool."""

    def __init__(
        self,
        database_url: str,
        *,
        read_only: bool = False,
        min_size: int = 2,
        max_size: int = 10,
    ) -> None:
        self._database_url = database_url
        self._read_only = read_only
        self._min_size = min_size
        self._max_size = max_size
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            # SQLAlchemy async DSN uses postgresql+asyncpg:// — strip driver prefix for asyncpg
            url = self._database_url.replace("postgresql+asyncpg://", "postgresql://")
            server_settings = None
            if self._read_only:
                # Defence in depth for visitor-supplied databases: the session itself
                # refuses writes and runaway queries, regardless of the SQL validator.
                server_settings = {
                    "default_transaction_read_only": "on",
                    "statement_timeout": "15000",
                }
            self._pool = await asyncpg.create_pool(
                url,
                min_size=self._min_size,
                max_size=self._max_size,
                timeout=10,
                server_settings=server_settings,
            )
        return self._pool

    async def fetch_many(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *(params or ()))
            return [dict(row) for row in rows[:limit]]

    async def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, *(params or ()))
            return dict(row) if row else None

    async def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(sql, *(params or ()))

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_database_service() -> DatabaseProtocol:
    # Cached: one service (and one connection pool) for the whole process. Building a new
    # one per call leaked a pool of connections on every request.
    from app.config import settings
    if settings.use_mock_sql:
        logger.info("DatabaseService: using MockDatabaseService")
        return MockDatabaseService()
    if settings.database_url.startswith("sqlite"):
        # sqlite:///./agentflow.db -> ./agentflow.db
        path = settings.database_url.split("///", 1)[-1]
        logger.info("DatabaseService: using local SQLite at %s", path)
        return SqliteService(path)
    logger.info("DatabaseService: connecting to PostgreSQL at %s", settings.database_url)
    return PostgresService(settings.database_url)

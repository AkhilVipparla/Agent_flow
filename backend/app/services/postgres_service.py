from __future__ import annotations

import logging
import os
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

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# Mock — returns realistic rows without a running PostgreSQL instance.
# ---------------------------------------------------------------------------

_MOCK_AGENT_RUNS: list[dict[str, Any]] = [
    {"id": "run-001", "agent_name": "rag",    "status": "complete", "duration_ms": 1240, "evidence_count": 5,  "report_id": "rep-001"},
    {"id": "run-002", "agent_name": "sql",    "status": "complete", "duration_ms": 890,  "evidence_count": 3,  "report_id": "rep-001"},
    {"id": "run-003", "agent_name": "search", "status": "complete", "duration_ms": 2100, "evidence_count": 4,  "report_id": "rep-002"},
    {"id": "run-004", "agent_name": "rag",    "status": "failed",   "duration_ms": 300,  "evidence_count": 0,  "report_id": "rep-003"},
    {"id": "run-005", "agent_name": "critic", "status": "complete", "duration_ms": 540,  "evidence_count": 0,  "report_id": "rep-002"},
]

_MOCK_USAGE: list[dict[str, Any]] = [
    {"org_id": "org-001", "org_name": "Acme Corp",     "tokens_used": 142000, "cost_usd": 1.42, "report_count": 34},
    {"org_id": "org-002", "org_name": "Globex Inc",    "tokens_used": 98500,  "cost_usd": 0.99, "report_count": 21},
    {"org_id": "org-003", "org_name": "Initech Ltd",   "tokens_used": 211300, "cost_usd": 2.11, "report_count": 58},
    {"org_id": "org-004", "org_name": "Umbrella Corp", "tokens_used": 67800,  "cost_usd": 0.68, "report_count": 15},
]

_MOCK_REPORTS: list[dict[str, Any]] = [
    {"id": "rep-001", "query": "Q4 revenue breakdown",           "confidence_score": 0.91, "created_at": "2025-01-15T10:23:00Z"},
    {"id": "rep-002", "query": "Customer churn analysis",        "confidence_score": 0.85, "created_at": "2025-01-18T14:05:00Z"},
    {"id": "rep-003", "query": "Infrastructure cost optimisation","confidence_score": 0.72, "created_at": "2025-01-20T09:47:00Z"},
    {"id": "rep-004", "query": "Product roadmap feasibility",    "confidence_score": 0.88, "created_at": "2025-01-22T16:30:00Z"},
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
        rows = await self.fetch_many(sql, params, limit=1)
        return rows[0] if rows else None

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Real — asyncpg connection pool; lazy init.
# ---------------------------------------------------------------------------

class PostgresService:
    """Real PostgreSQL service using asyncpg connection pool."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            # SQLAlchemy async DSN uses postgresql+asyncpg:// — strip driver prefix for asyncpg
            url = self._database_url.replace("postgresql+asyncpg://", "postgresql://")
            self._pool = await asyncpg.create_pool(url, min_size=2, max_size=10)
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

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_database_service() -> DatabaseProtocol:
    use_mock = os.getenv("USE_MOCK_SQL", "true").lower() not in ("false", "0", "no")
    if use_mock:
        logger.info("DatabaseService: using MockDatabaseService")
        return MockDatabaseService()
    from app.config import settings
    logger.info("DatabaseService: connecting to PostgreSQL at %s", settings.database_url)
    return PostgresService(settings.database_url)

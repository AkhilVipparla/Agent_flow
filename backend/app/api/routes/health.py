from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.postgres_service import get_database_service
from app.services.qdrant_service import get_vector_search_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

_CHECK_TIMEOUT_SECONDS = 3.0


@router.get("/health")
async def health() -> dict:
    """Liveness: the process is up and serving. Does no I/O, so a slow dependency never
    makes the platform restart a perfectly healthy server."""
    return {"status": "ok"}


async def _check(name: str, probe) -> tuple[str, str]:
    try:
        await asyncio.wait_for(probe(), timeout=_CHECK_TIMEOUT_SECONDS)
        return name, "ok"
    except Exception as exc:
        # Which dependency is down is useful; why (it can contain hostnames) goes to the log only.
        logger.warning("Readiness check %r failed (%s)", name, type(exc).__name__)
        return name, "unavailable"


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness: can this instance serve real requests? Checks the database and the vector
    store; answers 503 when either is down so a load balancer stops routing here."""
    db = get_database_service()
    vectors = get_vector_search_service()

    async def probe_db() -> None:
        await db.fetch_one("SELECT 1")

    results = await asyncio.gather(_check("database", probe_db), _check("vector_store", vectors.ping))
    checks = dict(results)
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "degraded", "checks": checks},
    )

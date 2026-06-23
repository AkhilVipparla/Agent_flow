from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import DbDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(db: DbDep) -> dict:
    checks: dict[str, str] = {}
    try:
        await db.fetch_one("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}

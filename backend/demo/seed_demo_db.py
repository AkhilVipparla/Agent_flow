"""Load the sample retail data into the database named by DEMO_DATABASE_URL.

Usage (from the backend/ directory):
    PYTHONPATH=. python demo/seed_demo_db.py

The target database must already exist (create it once with your Postgres host's
tools, e.g. CREATE DATABASE agentflow_demo). Safe to re-run: it rebuilds its own tables.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from app.config import settings


async def main() -> None:
    if not settings.demo_database_url:
        raise SystemExit("DEMO_DATABASE_URL is not set.")
    url = settings.demo_database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        await conn.execute((Path(__file__).parent / "demo_seed.sql").read_text(encoding="utf-8"))
        counts = {
            t: await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
            for t in ("customers", "products", "orders", "order_items")
        }
        print("Demo data loaded:", counts)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

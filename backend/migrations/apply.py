"""Apply pending SQL migrations to the database in DATABASE_URL.

Usage (from the backend/ directory):
    PYTHONPATH=. python migrations/apply.py            # apply what is pending
    PYTHONPATH=. python migrations/apply.py --status   # show applied / pending, change nothing

Each file runs once, in filename order, inside its own transaction: a failing migration
changes nothing and stops the run. Applied files are recorded in `schema_migrations`.
An advisory lock stops two deploys from migrating at the same time.

Files 001-003 predate this tracking and are idempotent (IF NOT EXISTS), so on a database that
already has them, the first run simply re-applies and records them.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import asyncpg

from app.config import settings

MIGRATIONS_DIR = Path(__file__).parent
_LOCK_ID = 727_274  # arbitrary constant shared by every migrator


async def main(status_only: bool = False) -> int:
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        await conn.execute("SELECT pg_advisory_lock($1)", _LOCK_ID)
        applied = {row["version"] for row in await conn.fetch("SELECT version FROM schema_migrations")}
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        pending = [f for f in files if f.name not in applied]

        if status_only:
            for f in files:
                print(f"{'applied' if f.name in applied else 'PENDING':8} {f.name}")
            return 0

        if not pending:
            print("Database is up to date.")
            return 0

        for sql_file in pending:
            print(f"Applying {sql_file.name} ...")
            async with conn.transaction():
                await conn.execute(sql_file.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations (version) VALUES ($1)", sql_file.name)
        print(f"Applied {len(pending)} migration(s).")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(status_only="--status" in sys.argv)))

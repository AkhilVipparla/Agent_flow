"""Apply SQL migrations to the database in DATABASE_URL.

Usage (from the backend/ directory):
    python migrations/apply.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from app.config import settings


async def main() -> None:
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        for sql_file in sorted(Path(__file__).parent.glob("*.sql")):
            print(f"Applying {sql_file.name} ...")
            await conn.execute(sql_file.read_text(encoding="utf-8"))
        print("Migrations applied successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

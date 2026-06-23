"""CLI entry point for database migrations."""
import asyncio
import os

from seja_mcp.db.connection import close_all
from seja_mcp.db.schema import run_migrations

DB_PATH = os.environ.get("SEJA_DB_PATH", os.path.expanduser("~/.seja-state/seja.db"))


async def _run():
    try:
        await run_migrations(DB_PATH)
    finally:
        await close_all()


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()

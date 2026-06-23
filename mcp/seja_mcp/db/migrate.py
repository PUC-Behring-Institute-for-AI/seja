"""CLI entry point for database migrations."""
import asyncio
import os

from seja_mcp.db.schema import run_migrations

DB_PATH = os.environ.get("SEJA_DB_PATH", os.path.expanduser("~/.seja-state/seja.db"))


def main():
    asyncio.run(run_migrations(DB_PATH))


if __name__ == "__main__":
    main()

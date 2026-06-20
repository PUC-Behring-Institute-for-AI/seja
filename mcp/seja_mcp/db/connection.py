import os
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = os.environ.get("SEJA_DB_PATH", os.path.expanduser("~/.seja-state/seja.db"))

_connection_pool: dict[str, aiosqlite.Connection] = {}

PRAGMAS = [
    "PRAGMA journal_mode=WAL",
    "PRAGMA foreign_keys=ON",
    "PRAGMA busy_timeout=5000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA cache_size=-64000",
    "PRAGMA mmap_size=268435456",
    "PRAGMA wal_autocheckpoint=0",
]


def get_db_path(workspace_path: str = "") -> str:
    if workspace_path:
        state_dir = os.path.join(workspace_path, ".seja", "state")
        os.makedirs(state_dir, exist_ok=True)
        return os.path.join(state_dir, "seja.db")
    return DB_PATH


@asynccontextmanager
async def get_db(workspace_path: str = ""):
    db_path = get_db_path(workspace_path)
    if db_path not in _connection_pool or _connection_pool[db_path].closed:
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row
        for pragma in PRAGMAS:
            await conn.execute(pragma)
        _connection_pool[db_path] = conn
    try:
        yield _connection_pool[db_path]
    except Exception:
        await _connection_pool[db_path].rollback()
        raise
    finally:
        pass


async def close_all():
    for path, conn in _connection_pool.items():
        if not conn.closed:
            await conn.close()
    _connection_pool.clear()

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import DB_BACKEND, DEFAULT_TABLE

if DB_BACKEND == "postgres":
    from db import postgres_backend as _backend
elif DB_BACKEND == "sqlite":
    from db import sqlite_backend as _backend
else:
    raise ValueError(
        f"Unsupported DB_BACKEND={DB_BACKEND!r}. Use 'sqlite' or 'postgres'."
    )


def get_connection():
    return _backend.connect()


def init_db(conn) -> None:
    _backend.init_db(conn)


def fetch_all(conn, table: str = DEFAULT_TABLE) -> list[dict[str, Any]]:
    return _backend.fetch_all(conn, table)


def get_applied_patches(conn) -> set[str]:
    return _backend.get_applied_patches(conn)


def mark_patch_applied(conn, filename: str) -> None:
    _backend.mark_patch_applied(conn, filename)


def upsert_rows(conn, table: str, rows: list[dict[str, Any]]) -> tuple[int, int]:
    return _backend.upsert_rows(conn, table, rows)


def run_sql(conn, sql: str) -> int:
    return _backend.run_sql(conn, sql)


def run_sql_file(conn, path: Path) -> int:
    return _backend.run_sql_file(conn, path)


def rollback(conn) -> None:
    _backend.rollback(conn)

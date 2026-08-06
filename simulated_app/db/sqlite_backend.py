from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DB_PATH, DEFAULT_TABLE


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {DEFAULT_TABLE} (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS applied_patches (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def fetch_all(conn: sqlite3.Connection, table: str = DEFAULT_TABLE) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def get_applied_patches(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT filename FROM applied_patches").fetchall()
    return {row["filename"] for row in rows}


def mark_patch_applied(conn: sqlite3.Connection, filename: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO applied_patches (filename, applied_at) VALUES (?, ?)",
        (filename, now),
    )
    conn.commit()


def upsert_rows(
    conn: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    updated = 0

    for row in rows:
        row_id = row.get("id")
        if row_id is None:
            continue

        name = row.get("name", "")
        status = row.get("status", "active")
        existing = conn.execute(
            f"SELECT id FROM {table} WHERE id = ?", (row_id,)
        ).fetchone()

        if existing:
            conn.execute(
                f"""
                UPDATE {table}
                SET name = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, status, now, row_id),
            )
            updated += 1
        else:
            conn.execute(
                f"""
                INSERT INTO {table} (id, name, status, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (row_id, name, status, now),
            )
            inserted += 1

    conn.commit()
    return inserted, updated


def run_sql(conn: sqlite3.Connection, sql: str) -> int:
    before = conn.total_changes
    conn.executescript(sql)
    conn.commit()
    return conn.total_changes - before


def run_sql_file(conn: sqlite3.Connection, path: Path) -> int:
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{path.name}: SQL file is empty")
    return run_sql(conn, sql)

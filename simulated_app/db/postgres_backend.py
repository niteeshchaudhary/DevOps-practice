from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import (
    DATABASE_URL,
    DEFAULT_TABLE,
    PGDATABASE,
    PGHOST,
    PGPASSWORD,
    PGPORT,
    PGUSER,
)


def _connect_kwargs() -> dict[str, Any]:
    if DATABASE_URL:
        return {"dsn": DATABASE_URL}
    return {
        "host": PGHOST,
        "port": PGPORT,
        "dbname": PGDATABASE,
        "user": PGUSER,
        "password": PGPASSWORD,
    }


def connect():
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError as exc:
        raise ImportError(
            "Postgres backend requires psycopg2. Install with: pip install psycopg2-binary"
        ) from exc

    kwargs = _connect_kwargs()
    if "dsn" in kwargs:
        conn = psycopg2.connect(kwargs["dsn"], cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(cursor_factory=RealDictCursor, **kwargs)
    conn.autocommit = False
    return conn


def rollback(conn) -> None:
    conn.rollback()


def init_db(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DEFAULT_TABLE} (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS applied_patches (
                filename TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
    conn.commit()


def fetch_all(conn, table: str = DEFAULT_TABLE) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table} ORDER BY id")
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_applied_patches(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM applied_patches")
        rows = cur.fetchall()
    return {row["filename"] for row in rows}


def mark_patch_applied(conn, filename: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO applied_patches (filename, applied_at)
                VALUES (%s, %s)
                ON CONFLICT (filename) DO UPDATE SET applied_at = EXCLUDED.applied_at
                """,
                (filename, now),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def upsert_rows(conn, table: str, rows: list[dict[str, Any]]) -> tuple[int, int]:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    updated = 0

    try:
        with conn.cursor() as cur:
            for row in rows:
                row_id = row.get("id")
                if row_id is None:
                    continue

                name = row.get("name", "")
                status = row.get("status", "active")

                cur.execute(f"SELECT id FROM {table} WHERE id = %s", (row_id,))
                existing = cur.fetchone()

                if existing:
                    cur.execute(
                        f"""
                        UPDATE {table}
                        SET name = %s, status = %s, updated_at = %s
                        WHERE id = %s
                        """,
                        (name, status, now, row_id),
                    )
                    updated += 1
                else:
                    cur.execute(
                        f"""
                        INSERT INTO {table} (id, name, status, updated_at)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (row_id, name, status, now),
                    )
                    inserted += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return inserted, updated


def _split_sql(sql: str) -> list[str]:
    """Naive statement split on ';' — fine for simple patch scripts."""
    parts = []
    for chunk in sql.split(";"):
        stmt = chunk.strip()
        if not stmt or stmt.startswith("--"):
            # keep multi-line comments with content after
            lines = [
                ln for ln in stmt.splitlines()
                if ln.strip() and not ln.strip().startswith("--")
            ]
            stmt = "\n".join(lines).strip()
        if stmt:
            parts.append(stmt)
    return parts


def run_sql(conn, sql: str) -> int:
    affected = 0
    try:
        with conn.cursor() as cur:
            for stmt in _split_sql(sql):
                cur.execute(stmt)
                if cur.rowcount and cur.rowcount > 0:
                    affected += cur.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return affected


def run_sql_file(conn, path: Path) -> int:
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{path.name}: SQL file is empty")
    return run_sql(conn, sql)

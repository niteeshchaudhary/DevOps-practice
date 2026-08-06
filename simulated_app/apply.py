#!/usr/bin/env python3
"""Apply a SQL (or data) patch file against the configured database.

Usage:
  ./apply apply.sql
  ./apply 005_sql_example.sql
  python apply.py patches/005_fix.sql --force

Backend is chosen via DB_BACKEND=sqlite|postgres (see config / .env.example).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import DEFAULT_TABLE, PATCHES_DIR, db_display_name
from db.database import (
    get_applied_patches,
    get_connection,
    init_db,
    mark_patch_applied,
    run_sql,
    run_sql_file,
    upsert_rows,
)
from loaders.registry import discover_loaders, load_patch_file


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if path.exists():
        return path.resolve()

    candidate = PATCHES_DIR / raw
    if candidate.exists():
        return candidate.resolve()

    raise FileNotFoundError(f"File not found: {raw} (also checked {PATCHES_DIR}/)")


def apply_one(path: Path, *, force: bool = False, record: bool = True) -> None:
    conn = get_connection()
    init_db(conn)

    name = path.name
    applied = get_applied_patches(conn)

    if record and not force and name in applied:
        print(f"skip  {name} (already applied; use --force to re-run)")
        return

    label = db_display_name()

    if path.suffix.lower() == ".sql":
        affected = run_sql_file(conn, path)
    else:
        registry = discover_loaders(Path(__file__).resolve().parent / "loaders")
        payload = load_patch_file(path, registry)
        if payload.get("type") == "sql":
            affected = run_sql(conn, payload["sql"])
        else:
            table = payload.get("table", DEFAULT_TABLE)
            inserted, updated = upsert_rows(conn, table, payload.get("rows", []))
            if record:
                mark_patch_applied(conn, name)
            print(f"ok    {name}  (+{inserted} / ~{updated})  db={label}")
            return

    if record:
        mark_patch_applied(conn, name)
    print(f"ok    {name}  (sql, ~{affected} changes)  db={label}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apply",
        description="Connect to the configured DB and apply a patch (SQL / JSON / CSV).",
    )
    parser.add_argument("file", help="Path to patch file, or a name under patches/")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if this filename was already recorded as applied",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Run without marking it in applied_patches",
    )
    args = parser.parse_args(argv)

    try:
        path = resolve_path(args.file)
        apply_one(path, force=args.force, record=not args.no_record)
    except Exception as exc:
        print(f"error {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

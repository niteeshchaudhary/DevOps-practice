from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import DEFAULT_TABLE, PATCHES_DIR
from db.database import get_applied_patches, mark_patch_applied, rollback, run_sql, upsert_rows
from loaders.registry import discover_loaders, load_patch_file


@dataclass
class PatchResult:
    filename: str
    inserted: int
    updated: int
    skipped: bool = False
    error: str | None = None
    kind: str = "rows"  # rows | sql


def list_patch_files(patches_dir: Path = PATCHES_DIR) -> list[Path]:
    patches_dir.mkdir(parents=True, exist_ok=True)
    supported = {".json", ".csv", ".sql"}
    files = [
        p for p in patches_dir.iterdir()
        if p.is_file() and p.suffix.lower() in supported and not p.name.startswith(".")
    ]
    return sorted(files, key=lambda p: p.name)


def apply_patches(conn: Any) -> list[PatchResult]:
    rollback(conn)  # clear aborted txn from a prior failed patch (cached Streamlit conn)

    registry = discover_loaders(Path(__file__).resolve().parent.parent / "loaders")
    applied = get_applied_patches(conn)
    results: list[PatchResult] = []

    for patch_file in list_patch_files():
        if patch_file.name in applied:
            results.append(PatchResult(patch_file.name, 0, 0, skipped=True))
            continue

        try:
            payload = load_patch_file(patch_file, registry)

            if payload.get("type") == "sql":
                affected = run_sql(conn, payload["sql"])
                mark_patch_applied(conn, patch_file.name)
                results.append(
                    PatchResult(patch_file.name, affected, 0, kind="sql")
                )
            else:
                table = payload.get("table", DEFAULT_TABLE)
                rows = payload.get("rows", [])
                inserted, updated = upsert_rows(conn, table, rows)
                mark_patch_applied(conn, patch_file.name)
                results.append(PatchResult(patch_file.name, inserted, updated))
        except Exception as exc:
            rollback(conn)
            results.append(PatchResult(patch_file.name, 0, 0, error=str(exc)))

    return results

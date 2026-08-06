from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PATCHES_DIR = BASE_DIR / "patches"
LOADERS_DIR = BASE_DIR / "loaders"
DB_PATH = DATA_DIR / "app.db"

DEFAULT_TABLE = "items"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no extra dependency). Does not override existing env."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

# sqlite | postgres
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").strip().lower()

# Postgres: prefer DATABASE_URL, else discrete vars
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "simulated_app")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")


def db_display_name() -> str:
    if DB_BACKEND == "postgres":
        if DATABASE_URL:
            safe = DATABASE_URL
            if "@" in safe and "://" in safe:
                scheme, rest = safe.split("://", 1)
                if "@" in rest and ":" in rest.split("@", 1)[0]:
                    userinfo, hostpart = rest.split("@", 1)
                    user = userinfo.split(":", 1)[0]
                    safe = f"{scheme}://{user}:***@{hostpart}"
            return f"postgres ({safe})"
        return f"postgres ({PGUSER}@{PGHOST}:{PGPORT}/{PGDATABASE})"
    return f"sqlite ({DB_PATH.name})"

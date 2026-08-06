from __future__ import annotations

from pathlib import Path
from typing import Any

from loaders.base import BaseLoader


class SqlLoader(BaseLoader):
    """Load raw .sql patch files. Payload uses type=sql so the apply service runs queries."""

    extensions = (".sql",)

    def load(self, path: Path) -> dict[str, Any]:
        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            raise ValueError(f"{path.name}: SQL file is empty")
        return {"type": "sql", "sql": sql}

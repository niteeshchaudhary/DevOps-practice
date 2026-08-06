from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loaders.base import BaseLoader


class JsonLoader(BaseLoader):
    extensions = (".json",)

    def load(self, path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        if "rows" not in data:
            raise ValueError(f"{path.name}: patch must contain a 'rows' list")

        return {
            "table": data.get("table", "items"),
            "rows": data["rows"],
        }

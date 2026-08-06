from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from loaders.base import BaseLoader


class CsvLoader(BaseLoader):
    extensions = (".csv",)

    def load(self, path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                parsed = dict(row)
                if "id" in parsed and parsed["id"]:
                    parsed["id"] = int(parsed["id"])
                rows.append(parsed)

        return {"table": "items", "rows": rows}

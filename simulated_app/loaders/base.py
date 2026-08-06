from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseLoader(ABC):
    """Base class for patch file loaders. Subclass and set `extensions`."""

    extensions: tuple[str, ...] = ()

    @abstractmethod
    def load(self, path: Path) -> dict[str, Any]:
        """
        Load a patch file and return:
          {"table": "items", "rows": [{"id": 1, "name": "...", "status": "..."}]}
        """
        ...

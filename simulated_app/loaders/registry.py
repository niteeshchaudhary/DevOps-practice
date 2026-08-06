from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any

from loaders.base import BaseLoader


def discover_loaders(loaders_dir: Path) -> dict[str, BaseLoader]:
    """
    Auto-discover loader classes from the loaders/ package.
    Add a new file (e.g. yaml_loader.py) with a BaseLoader subclass to support new formats.
    """
    registry: dict[str, BaseLoader] = {}

    import loaders as loaders_pkg

    for module_info in pkgutil.iter_modules(loaders_pkg.__path__):
        if module_info.name in ("base", "registry"):
            continue

        module = importlib.import_module(f"loaders.{module_info.name}")
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseLoader)
                and obj is not BaseLoader
            ):
                loader = obj()
                for ext in loader.extensions:
                    registry[ext] = loader

    return registry


def load_patch_file(path: Path, registry: dict[str, BaseLoader]) -> dict[str, Any]:
    ext = path.suffix.lower()
    loader = registry.get(ext)
    if loader is None:
        raise ValueError(f"No loader registered for {ext} ({path.name})")
    return loader.load(path)

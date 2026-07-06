from __future__ import annotations

from pathlib import Path


def clean_object_name(path: Path) -> str:
    name = path.name

    if name.lower().endswith((".html", ".htm")):
        name = Path(name).stem

    return name.replace("_", " ").replace("-", " ").strip() or path.name

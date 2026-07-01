from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".jarvis",
    "$RECYCLE.BIN",
    "System Volume Information",
}


def discover_files(root: Path) -> Iterable[Path]:
    root = root.expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Knowledge root does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Knowledge root is not a directory: {root}")

    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        if path.is_file():
            yield path

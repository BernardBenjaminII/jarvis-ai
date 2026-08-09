from __future__ import annotations

import os
from pathlib import Path

from .contracts import RepositoryNotFoundError


MARKERS = ("core", "dev", "docs")


def is_repository_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in MARKERS)


def discover_repository_root(start: str | Path | None = None) -> Path:
    candidates: list[Path] = []

    explicit = os.environ.get("JARVIS_PROJECT_ROOT")
    if explicit:
        candidates.append(Path(explicit))

    if start is not None:
        candidates.append(Path(start))

    candidates.extend((Path.cwd(), Path(__file__).resolve()))

    seen: set[Path] = set()

    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate.is_file():
            candidate = candidate.parent

        for path in (candidate, *candidate.parents):
            if path in seen:
                continue
            seen.add(path)

            if is_repository_root(path):
                return path

    raise RepositoryNotFoundError(
        "Unable to locate a repository containing core/, dev/, and docs/."
    )


def discover_runtime_root(repository_root: Path) -> Path | None:
    candidates = (
        os.environ.get("JARVIS_RUNTIME_ROOT"),
        "/media/abdullah/JARVIS_RUNTIME_L",
        str(repository_root / ".runtime"),
    )

    for value in candidates:
        if value:
            path = Path(value).expanduser().resolve()
            if path.exists():
                return path

    return None


def discover_knowledge_root(
    repository_root: Path,
    runtime_root: Path | None,
) -> Path | None:
    candidates: list[str | None] = [
        os.environ.get("JARVIS_KNOWLEDGE_ROOT"),
    ]

    if runtime_root is not None:
        candidates.append(str(runtime_root / "knowledge"))

    candidates.extend(
        (
            "/media/abdullah/JARVISDATA/Knowledge",
            str(repository_root / "knowledge"),
        )
    )

    for value in candidates:
        if value:
            path = Path(value).expanduser().resolve()
            if path.exists():
                return path

    return None

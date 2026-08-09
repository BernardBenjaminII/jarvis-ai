from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from .context import RuntimeContext
from .environment import (
    python_executable,
    python_version,
    runtime_platform,
)
from .errors import (
    GenesisBootstrapError,
    GenesisRepositoryNotFoundError,
)
from .validation import ensure_repository_layout


def _candidate_roots(start: Path) -> Iterable[Path]:
    resolved = start.expanduser().resolve()

    if resolved.is_file():
        resolved = resolved.parent

    yield resolved
    yield from resolved.parents


def locate_project_root(
    start: Path | str | None = None,
) -> Path:
    explicit = os.environ.get("JARVIS_PROJECT_ROOT")

    if explicit:
        return ensure_repository_layout(Path(explicit))

    origin = Path(start) if start is not None else Path(__file__)

    for candidate in _candidate_roots(origin):
        try:
            return ensure_repository_layout(candidate)
        except Exception:
            continue

    cwd = Path.cwd()

    for candidate in _candidate_roots(cwd):
        try:
            return ensure_repository_layout(candidate)
        except Exception:
            continue

    raise GenesisRepositoryNotFoundError(
        "Unable to locate the canonical JARVIS repository from "
        f"start={origin!s} or cwd={cwd!s}. "
        "Set JARVIS_PROJECT_ROOT to the repository path if necessary."
    )


def _insert_project_root(root: Path) -> None:
    root_text = str(root)
    matches = [
        index
        for index, value in enumerate(sys.path)
        if value == root_text
    ]

    for index in reversed(matches):
        del sys.path[index]

    sys.path.insert(0, root_text)


def _discover_genesis_version(root: Path) -> str | None:
    candidates = (
        root / "GENESIS_VERSION",
        root / "docs" / "GENESIS_VERSION",
        root / "VERSION",
    )

    for path in candidates:
        if path.is_file():
            value = path.read_text(
                encoding="utf-8",
            ).strip()

            if value:
                return value

    return None


def bootstrap_runtime(
    start: Path | str | None = None,
) -> RuntimeContext:
    try:
        root = locate_project_root(start)
        _insert_project_root(root)

        return RuntimeContext(
            project_root=root,
            python_executable=python_executable(),
            python_version=python_version(),
            working_directory=Path.cwd().resolve(),
            platform=runtime_platform(),
            repository_verified=True,
            genesis_version=_discover_genesis_version(root),
        )
    except Exception as exc:
        if isinstance(exc, GenesisRepositoryNotFoundError):
            raise

        raise GenesisBootstrapError(
            f"Genesis runtime bootstrap failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

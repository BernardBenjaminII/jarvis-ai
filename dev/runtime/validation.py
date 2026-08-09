from __future__ import annotations

from pathlib import Path

from .errors import GenesisRepositoryValidationError


REQUIRED_DIRECTORIES = ("core", "dev", "docs")
REQUIRED_FILES = ("core/__init__.py",)


def ensure_repository_layout(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    missing: list[str] = []

    for name in REQUIRED_DIRECTORIES:
        if not (resolved / name).is_dir():
            missing.append(f"{name}/")

    for name in REQUIRED_FILES:
        if not (resolved / name).is_file():
            missing.append(name)

    if missing:
        raise GenesisRepositoryValidationError(
            "Candidate repository is not canonical. Missing: "
            + ", ".join(missing)
            + f". Candidate: {resolved}"
        )

    return resolved

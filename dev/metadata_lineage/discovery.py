from __future__ import annotations

from pathlib import Path


def discover_databases(
    *,
    project_root: Path,
    knowledge_root: Path | None,
) -> tuple[Path, ...]:
    candidates: set[Path] = set()
    roots = [
        project_root,
        project_root / "data",
        project_root / "runtime",
        project_root / "knowledge",
    ]

    if knowledge_root is not None:
        roots.append(knowledge_root)

    for root in roots:
        if not root.exists():
            continue

        for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
            for path in root.rglob(pattern):
                if ".migration_backups" in path.parts:
                    continue
                if path.is_file():
                    candidates.add(path.resolve())

    return tuple(sorted(candidates))

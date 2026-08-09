from __future__ import annotations
from pathlib import Path

def candidate_databases(
    project_root: Path,
    runtime_catalog: Path,
    knowledge_root: Path,
) -> tuple[Path, ...]:
    roots = (
        project_root / ".runtime",
        runtime_catalog.parent,
        knowledge_root,
        knowledge_root / ".jarvis",
        runtime_catalog.parent / "backups",
    )
    found: set[Path] = {runtime_catalog.resolve()}
    for root in roots:
        if not root.exists():
            continue
        for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
            for path in root.rglob(pattern):
                if path.is_file() and ".migration_backups" not in path.parts:
                    try:
                        if path.open("rb").read(16) == b"SQLite format 3\x00":
                            found.add(path.resolve())
                    except OSError:
                        pass
    return tuple(sorted(found))

from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = ROOT / "archive" / "phase_ii_a_backups"

PATTERNS = [
    "*.bak",
    "*.pre_resource_refactor.bak",
    "*.resource_v1.bak",
    "*.resource_working.bak",
    "*.monolith.bak",
]


def find_backups() -> list[Path]:
    results: list[Path] = []

    for pattern in PATTERNS:
        results.extend(ROOT.rglob(pattern))

    ignored_parts = {
        ".git",
        "__pycache__",
        "archive",
    }

    clean = []
    for path in sorted(set(results)):
        if any(part in ignored_parts for part in path.parts):
            continue
        clean.append(path)

    return clean


def archive_file(path: Path) -> Path:
    relative = path.relative_to(ROOT)
    destination = ARCHIVE_ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))
    return destination


def main() -> int:
    backups = find_backups()

    print("\nPhase II-A Backup Archiver")
    print("=" * 40)

    if not backups:
        print("No backup files to archive.")
        return 0

    for path in backups:
        destination = archive_file(path)
        print(f"ARCHIVED {path.relative_to(ROOT)} -> {destination.relative_to(ROOT)}")

    print("\nBackup archival complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

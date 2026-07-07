#!/usr/bin/env python3
"""
Mark duplicate ADRs as legacy.

This script preserves historical ADR numbering while making it explicit
that duplicate numbers belong to the pre-governance era.
"""

from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = ROOT / "docs" / "decisions"

LEGACY_NOTICE = """
> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

"""

groups = defaultdict(list)

for path in sorted(ADR_DIR.glob("ADR-*")):
    if path.is_dir():
        continue

    parts = path.stem.split("-")

    if len(parts) < 2:
        continue

    number = "-".join(parts[:2])
    groups[number].append(path)

updated = 0

for number, files in sorted(groups.items()):

    if len(files) <= 1:
        continue

    print(f"{number}: {len(files)} duplicate ADRs")

    for file in files:

        text = file.read_text(encoding="utf-8")

        if "Legacy ADR" in text:
            continue

        lines = text.splitlines()

        insert_at = 1

        while insert_at < len(lines):

            line = lines[insert_at].strip()

            if line == "":
                insert_at += 1
                continue

            if line.startswith("##"):
                break

            insert_at += 1

        new_lines = (
            lines[:insert_at]
            + [""]
            + LEGACY_NOTICE.strip().splitlines()
            + [""]
            + lines[insert_at:]
        )

        file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        print(f"  updated {file.name}")
        updated += 1

print()
print(f"Updated {updated} ADR files.")

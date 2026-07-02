#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path("docs/architecture_blueprint")


def slugify(title: str) -> str:
    s = title.strip().replace(" ", "-")
    s = re.sub(r"[^A-Za-z0-9._-]+", "", s)
    return s


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new JARVIS Architecture Blueprint document.")
    parser.add_argument("number", help="Blueprint number, e.g. 0007")
    parser.add_argument("title", help="Blueprint title")
    args = parser.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)

    number = args.number.zfill(4)
    title = args.title.strip()
    path = ROOT / f"AB-{number}-{slugify(title)}.md"

    if path.exists():
        raise SystemExit(f"File already exists: {path}")

    path.write_text(
        f"""# AB-{number}: {title}

## Status

Draft

## Purpose

TODO

## Context

TODO

## Design

TODO

## Open Questions

TODO

## Related ADRs

TODO
""",
        encoding="utf-8",
    )

    print(f"[OK] Created {path}")


if __name__ == "__main__":
    main()

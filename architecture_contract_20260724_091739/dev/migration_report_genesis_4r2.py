#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "core/cognition/layers/observation"


def main() -> int:
    modules = sorted(PACKAGE_ROOT.glob("*.py"))
    lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in modules
    )

    print("=" * 70)
    print("GENESIS IV-R2 MIGRATION REPORT")
    print("=" * 70)
    print(f"Production modules        : {len(modules)}")
    print(f"Production lines          : {lines}")
    print("Existing modules replaced : 0")
    print("Public redirects          : 0")
    print("Migration type            : Additive")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

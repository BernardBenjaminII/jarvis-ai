#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/integration/bus.py",
    "core/integration/readiness.py",
    "core/integration/__init__.py",
    "core/src/routes/operations.py",
    "docs/architecture/executive_projection_bus.md",
    "docs/decisions/ADR-EXEC-0002-executive-projection-bus.md",
    "tests/test_genesis_vi_a3_executive_projection_bus.py",
    "dev/verify_genesis_vi_a3_executive_projection_bus.sh",
)


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0
    failures += check(all((ROOT / path).is_file() for path in REQUIRED), "Canonical VI-A3 file set")

    parse_ok = True
    for relative in (
        "core/integration/bus.py",
        "core/integration/readiness.py",
        "core/integration/__init__.py",
        "core/src/routes/operations.py",
        "tests/test_genesis_vi_a3_executive_projection_bus.py",
    ):
        try:
            ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        except Exception as exc:
            parse_ok = False
            print(f"[DETAIL] {relative}: {exc}")
    failures += check(parse_ok, "Python syntax structure")

    bus = (ROOT / "core/integration/bus.py").read_text(encoding="utf-8")
    failures += check(
        "class ExecutiveProjectionBus" in bus
        and "get_default_projection_bus" in bus
        and "fingerprint" in bus
        and "revision" in bus,
        "Projection Bus structure",
    )

    readiness = (ROOT / "core/integration/readiness.py").read_text(encoding="utf-8")
    failures += check(
        'GREEN = "green"' in readiness
        and 'YELLOW = "yellow"' in readiness
        and 'RED = "red"' in readiness,
        "Canonical readiness colors",
    )

    routes = (ROOT / "core/src/routes/operations.py").read_text(encoding="utf-8")
    failures += check(
        '@router.get("/bridge")' in routes
        and '@router.get("/bridge/readiness")' in routes
        and '@router.get("/bridge/manifest")' in routes,
        "Bridge route structure",
    )

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print("Overall status:", "EXCELLENT" if failures == 0 else "FAILED")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

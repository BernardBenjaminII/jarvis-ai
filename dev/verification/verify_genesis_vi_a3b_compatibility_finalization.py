#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    "core/src/routes/operations.py",
    "tests/test_genesis_vi_a3b_compatibility_finalization.py",
    "dev/verification/verify_genesis_vi_a3b_compatibility_finalization.py",
    "dev/verify_genesis_vi_a3b_compatibility_finalization.sh",
    "docs/architecture/genesis_vi_a3b_compatibility_finalization.md",
    "docs/decisions/ADR-EXEC-0004-ui-a2-route-compatibility.md",
)

EXPECTED_UI_A2_ROUTES = (
    '@router.get("/projections")',
    '@router.get("/projections/{projection_id}")',
    '@router.get("/capabilities")',
    '@router.get("/capabilities/{capability_name}")',
)

EXPECTED_BRIDGE_ROUTES = (
    '@router.get("/bridge")',
    '@router.get("/bridge/readiness")',
    '@router.get("/bridge/manifest")',
    '@router.get("/bridge/projections/{projection_id}")',
)


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0

    failures += check(
        all((ROOT / relative).is_file() for relative in REQUIRED),
        "Canonical VI-A3B file set",
    )

    parse_ok = True
    for relative in REQUIRED:
        path = ROOT / relative
        if path.suffix != ".py" or not path.is_file():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            parse_ok = False
            print(f"[DETAIL] {relative}: {exc}")
    failures += check(parse_ok, "Python syntax structure")

    source = (ROOT / "core/src/routes/operations.py").read_text(encoding="utf-8")
    failures += check(
        all(route in source for route in EXPECTED_UI_A2_ROUTES),
        "Exact UI-A2 compatibility route contract",
    )
    failures += check(
        all(route in source for route in EXPECTED_BRIDGE_ROUTES),
        "VI-A3 Bridge route contract preserved",
    )
    failures += check(
        "get_default_integration_runtime().projection_service" in source,
        "Compatibility routes delegate to canonical projection service",
    )
    failures += check(
        'operations_projection("capabilities")' in source,
        "Capabilities collection delegates to canonical capability projection",
    )

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print("Overall status:", "EXCELLENT" if failures == 0 else "FAILED")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

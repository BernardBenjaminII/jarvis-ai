#!/usr/bin/env python3
"""Structural verification for Genesis UI-A3."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "core/capabilities/__init__.py",
    "core/capabilities/discovery.py",
    "core/capabilities/metadata.py",
    "core/capabilities/operations.py",
    "core/integration/bootstrap.py",
    "core/integration/providers/capabilities.py",
    "core/integration/providers/operations.py",
    "tests/test_genesis_ui_a3_capability_discovery_registration.py",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    for relative in REQUIRED_FILES:
        path = ROOT / relative

        if not path.is_file():
            fail(f"Missing required file: {relative}")

        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            fail(f"Syntax error in {relative}: {exc}")

    bootstrap = (
        ROOT / "core/integration/bootstrap.py"
    ).read_text(encoding="utf-8")

    if "register_operations_capabilities" not in bootstrap:
        fail("Bootstrap does not register built-in Operations capabilities.")

    if "CapabilityDiscovery" not in bootstrap:
        fail("Bootstrap does not use recursive capability discovery.")

    provider = (
        ROOT / "core/integration/providers/capabilities.py"
    ).read_text(encoding="utf-8")

    for token in (
        '"bound"',
        '"unbound"',
        '"discovery"',
        '"registered_count"',
    ):
        if token not in provider:
            fail(f"Capability projection missing token: {token}")

    print("[PASS] Canonical UI-A3 file set")
    print("[PASS] Python syntax structure")
    print("[PASS] Built-in capability registration structure")
    print("[PASS] Recursive capability discovery structure")
    print("[PASS] Capability binding projection structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

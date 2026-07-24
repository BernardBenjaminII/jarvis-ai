#!/usr/bin/env python3
"""Certification for Genesis VI-A6.2."""

from __future__ import annotations

import ast
import hashlib
import importlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = (
    "core/executive/persistence/canonical.py",
    "core/executive/persistence/serializer.py",
    "tests/test_genesis_vi_a62_canonical_serializer.py",
    "docs/architecture/cognition/genesis_vi_a62_canonical_snapshot_serializer.md",
)

FORBIDDEN = (
    "sqlite3",
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "ollama",
)


def run(command: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    text = (result.stdout + result.stderr).strip()
    return result.returncode == 0, text


def imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def fingerprint() -> str:
    from core.executive.persistence import CanonicalSnapshotSerializer

    serializer = CanonicalSnapshotSerializer()
    value = {
        "session_id": "session-certification",
        "sequence": 42,
        "created_at": datetime(
            2026, 7, 22, 19, 30, tzinfo=timezone.utc
        ),
        "states": ("observing", "reasoning", "planning"),
        "authority": {"execute": False, "recommend": True},
    }
    return hashlib.sha256(serializer.dumps(value).payload).hexdigest()


EXPECTED = "3876beeb3e060b74ce3601ce2d3906fa50f97e731cf37fc5facca3dd92742085"


def main() -> int:
    print()
    print("=" * 72)
    print("JARVIS — GENESIS VI-A6.2 CANONICAL SNAPSHOT SERIALIZER")
    print("=" * 72)

    failures = 0

    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        print(f"[FAIL] Missing required files: {missing}")
        failures += 1
    else:
        print("[PASS] Canonical Genesis VI-A6.2 file structure")

    passed, text = run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(ROOT / "core" / "executive" / "persistence"),
            str(
                ROOT
                / "tests"
                / "test_genesis_vi_a62_canonical_serializer.py"
            ),
        ]
    )
    print(
        f"[{'PASS' if passed else 'FAIL'}] "
        "Genesis VI-A6.2 package compilation"
    )
    if not passed:
        failures += 1
        print(text)

    violations = []
    for filename in ("canonical.py", "serializer.py"):
        path = ROOT / "core" / "executive" / "persistence" / filename
        for module in imports(path):
            if module.startswith(FORBIDDEN):
                violations.append(f"{filename}: {module}")
    if violations:
        print(f"[FAIL] Forbidden dependencies: {violations}")
        failures += 1
    else:
        print("[PASS] Storage, network, vendor, and model isolation")

    module = importlib.import_module("core.executive.persistence")
    expected_symbols = (
        "CanonicalSnapshotSerializer",
        "CanonicalizationError",
        "SerializedSnapshot",
        "SerializationError",
        "to_canonical_value",
    )
    absent = [
        symbol for symbol in expected_symbols
        if not hasattr(module, symbol)
    ]
    if absent:
        print(f"[FAIL] Missing public symbols: {absent}")
        failures += 1
    else:
        print("[PASS] Stable Genesis VI-A6.2 public imports")

    passed, text = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_vi_a62_canonical_serializer",
        ]
    )
    print(
        f"[{'PASS' if passed else 'FAIL'}] "
        "Genesis VI-A6.2 canonical serializer tests"
    )
    if not passed:
        failures += 1
        print(text)

    passed, text = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_vi_a61.py",
        ]
    )
    print(
        f"[{'PASS' if passed else 'FAIL'}] "
        "Genesis VI-A6.1 through VI-A1 regression"
    )
    if not passed:
        failures += 1
        print(text)

    actual = fingerprint()
    if actual == EXPECTED:
        print("[PASS] Deterministic canonical-payload fingerprint")
    else:
        print(
            "[FAIL] Fingerprint mismatch: "
            f"expected {EXPECTED}, got {actual}"
        )
        failures += 1

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        + ("EXCELLENT" if failures == 0 else "FAILED")
    )
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

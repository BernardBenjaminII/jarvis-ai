#!/usr/bin/env python3
"""Deterministic certification for Genesis VI-A1 Executive Telemetry."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from datetime import datetime, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REQUIRED_FILES = (
    "core/operations/enums.py",
    "core/operations/contracts.py",
    "core/operations/models.py",
    "core/operations/executive.py",
    "core/operations/service.py",
    "core/operations/__init__.py",
    "tests/test_genesis_vi_a1_executive_telemetry.py",
)

REQUIRED_EXPORTS = (
    "DefaultExecutiveProvider",
    "ExecutiveProvider",
    "ExecutiveSnapshot",
    "ExecutiveState",
    "ExecutiveTelemetryAdapter",
    "OperationsService",
    "OperationsSnapshot",
)


def report(name: str, passed: bool, detail: str = "") -> int:
    status = "PASS" if passed else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")
    return 0 if passed else 1


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def architecture_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative in REQUIRED_FILES[:-1]:
        path = ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    failures = 0

    print("=" * 72)
    print("JARVIS — GENESIS VI-A1 EXECUTIVE TELEMETRY CERTIFICATION")
    print("=" * 72)

    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).is_file()]
    failures += report(
        "Canonical Genesis VI-A1 file set",
        not missing,
        ", ".join(missing),
    )

    if missing:
        print("-" * 72)
        print(f"Checks failed : {failures}")
        print("Overall status: FAILED")
        print("=" * 72)
        return 1

    compilation = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            *REQUIRED_FILES,
        ]
    )
    failures += report(
        "Genesis VI-A1 package compilation",
        compilation.returncode == 0,
        compilation.stderr.strip(),
    )

    try:
        operations = importlib.import_module("core.operations")
        missing_exports = [
            name for name in REQUIRED_EXPORTS if not hasattr(operations, name)
        ]
        exported = set(getattr(operations, "__all__", ()))
        absent_from_all = [name for name in REQUIRED_EXPORTS if name not in exported]
        public_api_ok = not missing_exports and not absent_from_all
        detail_parts = []
        if missing_exports:
            detail_parts.append(f"missing attributes: {missing_exports}")
        if absent_from_all:
            detail_parts.append(f"missing from __all__: {absent_from_all}")
        failures += report(
            "Stable public Operations API",
            public_api_ok,
            "; ".join(detail_parts),
        )
    except Exception as exc:  # pragma: no cover - certification boundary
        operations = None
        failures += report(
            "Stable public Operations API",
            False,
            f"{type(exc).__name__}: {exc}",
        )

    if operations is not None:
        try:
            fixed_time = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)
            service = operations.OperationsService(clock=lambda: fixed_time)
            first = service.snapshot().to_dict()
            second = service.snapshot().to_dict()

            executive = first.get("executive")
            integration_ok = (
                isinstance(executive, dict)
                and executive.get("state") == "ready"
                and isinstance(executive.get("readiness"), (int, float))
            )
            failures += report(
                "Executive snapshot integration",
                integration_ok,
                json.dumps(executive, sort_keys=True) if executive else "missing",
            )

            required_legacy_fields = {
                "state",
                "missions",
                "health",
                "resources",
                "timeline",
                "alerts",
                "generated_at",
                "fingerprint",
            }
            failures += report(
                "Existing Operations payload compatibility",
                required_legacy_fields.issubset(first),
                f"missing: {sorted(required_legacy_fields.difference(first))}",
            )

            deterministic = (
                first == second
                and isinstance(first.get("fingerprint"), str)
                and len(first["fingerprint"]) == 64
            )
            failures += report(
                "Deterministic Operations snapshot",
                deterministic,
            )
        except Exception as exc:  # pragma: no cover - certification boundary
            failures += report(
                "Executive snapshot integration",
                False,
                f"{type(exc).__name__}: {exc}",
            )
            failures += report("Existing Operations payload compatibility", False)
            failures += report("Deterministic Operations snapshot", False)

    tests = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_vi_a1_executive_telemetry",
        ]
    )
    if tests.stdout:
        print(tests.stdout.rstrip())
    if tests.stderr:
        print(tests.stderr.rstrip())
    failures += report(
        "Genesis VI-A1 regression suite",
        tests.returncode == 0,
    )

    fingerprint = architecture_fingerprint()
    failures += report(
        "Deterministic architecture fingerprint",
        len(fingerprint) == 64,
        fingerprint,
    )

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

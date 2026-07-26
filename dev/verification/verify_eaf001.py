#!/usr/bin/env python3
"""Deterministic verifier for EAF-001."""

from __future__ import annotations

import hashlib
import json
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/executive_academy/README.md",
    "docs/executive_academy/EXECUTIVE_ACADEMY_CONSTITUTION.md",
    "docs/executive_academy/MASTER_PLAN.md",
    "docs/executive_academy/ROADMAP.md",
    "docs/executive_academy/registries/departments.yaml",
    "docs/executive_academy/registries/academies.yaml",
    "docs/executive_academy/registries/authority_tiers.yaml",
    "docs/executive_academy/registries/jurisdictions.yaml",
    "docs/executive_academy/registries/curriculum_registry.yaml",
    "docs/executive_academy/registries/competency_registry.yaml",
    "docs/executive_academy/registries/certification_registry.yaml",
    "docs/executive_academy/registries/coverage_registry.yaml",
    "core/academy/__init__.py",
    "core/academy/contracts.py",
    "core/academy/enums.py",
    "core/academy/errors.py",
    "core/academy/models.py",
    "core/academy/registry.py",
    "tests/academy/test_eaf001_constitutional_foundation.py",
)

PYTHON_FILES = tuple(
    item for item in REQUIRED_FILES
    if item.endswith(".py")
)

FORBIDDEN_RUNTIME_NAMES = (
    "service.py",
    "api.py",
    "routes.py",
    "scheduler.py",
    "worker.py",
    "database.py",
)


def pass_check(label: str) -> None:
    print(f"[PASS] {label}")


def fail_check(label: str, detail: str) -> None:
    print(f"[FAIL] {label}: {detail}")


def architecture_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative in sorted(REQUIRED_FILES):
        path = ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    failures = 0

    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).is_file()]
    if missing:
        failures += 1
        fail_check("Canonical EAF-001 file set", ", ".join(missing))
    else:
        pass_check("Canonical EAF-001 file set")

    try:
        for relative in PYTHON_FILES:
            py_compile.compile(str(ROOT / relative), doraise=True)
    except Exception as exc:
        failures += 1
        fail_check("Python compilation", str(exc))
    else:
        pass_check("Python compilation")

    runtime_intrusions = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "core/academy").glob("*.py")
        if path.name in FORBIDDEN_RUNTIME_NAMES
    ]
    if runtime_intrusions:
        failures += 1
        fail_check("Dormant runtime boundary", ", ".join(runtime_intrusions))
    else:
        pass_check("Dormant runtime boundary")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.academy.test_eaf001_constitutional_foundation",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures += 1
        fail_check("EAF-001 unit tests", result.stdout + result.stderr)
    else:
        pass_check("EAF-001 unit tests")

    fingerprint = architecture_fingerprint()
    fingerprint_path = ROOT / "docs/executive_academy/EAF001_FINGERPRINT.sha256"
    fingerprint_path.write_text(f"{fingerprint}  EAF-001\n", encoding="utf-8")
    pass_check(f"Deterministic architecture fingerprint — {fingerprint}")

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

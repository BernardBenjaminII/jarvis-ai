#!/usr/bin/env python3
"""Structural verification for Genesis IV-A3."""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    PROJECT_ROOT / "core/cognition/claim.py",
    PROJECT_ROOT / "core/cognition/claim_construction.py",
    PROJECT_ROOT / "core/cognition/claim_validation.py",
    PROJECT_ROOT / "tests/test_genesis_4a3_claim_construction.py",
    PROJECT_ROOT
    / "docs/architecture/genesis_iv_a3_claim_construction.md",
    PROJECT_ROOT
    / "docs/decisions/ADR-0019-genesis-iv-claim-constitution.md",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "core.executive",
    "core.planning",
    "core.reasoning",
    "api",
    "ui",
)


def verify_required_files() -> None:
    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in REQUIRED_FILES
        if not path.is_file()
    ]

    if missing:
        raise AssertionError(
            f"Missing Genesis IV-A3 files: {missing}"
        )


def verify_import_boundaries() -> None:
    cognition_files = (
        PROJECT_ROOT / "core/cognition/claim.py",
        PROJECT_ROOT / "core/cognition/claim_construction.py",
        PROJECT_ROOT / "core/cognition/claim_validation.py",
    )

    violations: list[str] = []

    for path in cognition_files:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            imported_modules: list[str] = []

            if isinstance(node, ast.Import):
                imported_modules.extend(
                    alias.name
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)

            for module_name in imported_modules:
                if module_name.startswith(
                    FORBIDDEN_IMPORT_PREFIXES
                ):
                    violations.append(
                        f"{path.name}: {module_name}"
                    )

    if violations:
        raise AssertionError(
            "Forbidden forward dependencies: "
            + ", ".join(violations)
        )


def verify_public_api() -> None:
    cognition = importlib.import_module("core.cognition")

    required_exports = (
        "GENESIS_IV_A3_SCHEMA_VERSION",
        "ClaimCandidate",
        "ClaimConstructionEngine",
        "ClaimConstructionPolicy",
        "ClaimConstructionResult",
        "ClaimKind",
        "ClaimPolarity",
        "ClaimPredicate",
        "ClaimRecord",
        "ClaimScope",
        "ClaimStatus",
        "construct_claim",
        "make_claim_id",
        "validate_claim_object",
        "validate_claim_record",
    )

    missing = [
        name
        for name in required_exports
        if not hasattr(cognition, name)
    ]

    if missing:
        raise AssertionError(
            f"Missing cognition public exports: {missing}"
        )


def run_unit_tests() -> None:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(PROJECT_ROOT / "tests"),
        pattern="test_genesis_4a3_claim_construction.py",
        top_level_dir=str(PROJECT_ROOT),
    )

    result = unittest.TextTestRunner(
        verbosity=1,
    ).run(suite)

    if not result.wasSuccessful():
        raise AssertionError(
            "Genesis IV-A3 unit tests failed."
        )


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))

    checks = (
        ("Required files", verify_required_files),
        ("Forward-only dependencies", verify_import_boundaries),
        ("Stable public API", verify_public_api),
        ("Claim-construction tests", run_unit_tests),
    )

    failures = 0

    print()
    print("=" * 70)
    print("JARVIS GENESIS IV-A3 — CLAIM CONSTRUCTION")
    print("=" * 70)

    for label, check in checks:
        try:
            check()
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {label}: {exc}")
        else:
            print(f"[PASS] {label}")

    print("-" * 70)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        + ("EXCELLENT" if failures == 0 else "FAILED")
    )
    print("=" * 70)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

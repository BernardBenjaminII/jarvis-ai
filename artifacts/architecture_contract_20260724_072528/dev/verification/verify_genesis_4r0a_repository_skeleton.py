#!/usr/bin/env python3
"""Verify Genesis IV-R0 Package A repository architecture."""

from __future__ import annotations

import importlib
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COGNITION_ROOT = PROJECT_ROOT / "core/cognition"

EXPECTED_PACKAGES = (
    "common",
    "layers",
    "layers.observation",
    "layers.evidence",
    "layers.claims",
    "layers.relationships",
    "layers.hypotheses",
    "layers.interpretation",
    "layers.reasoning",
    "layers.justification",
)
EXISTING_PRODUCTION_MODULES = (
    "contracts.py",
    "errors.py",
    "normalization.py",
    "serialization.py",
    "confidence.py",
    "extraction.py",
    "observation.py",
    "provenance.py",
    "evidence.py",
    "evidence_chain.py",
    "evidence_validation.py",
    "claim.py",
    "claim_construction.py",
    "claim_validation.py",
)

REQUIRED_DOCUMENTS = (
    PROJECT_ROOT / "ARCHITECTURE.md",
    PROJECT_ROOT
    / "docs/architecture/cognition/00_overview.md",
    PROJECT_ROOT
    / "docs/decisions/"
    "ADR-0020-genesis-iv-cognition-architecture-constitution.md",
)

REQUIRED_PUBLIC_EXPORTS = (
    "Observation",
    "EvidenceRecord",
    "EvidenceChain",
    "ProvenanceRecord",
    "ClaimRecord",
    "ClaimConstructionEngine",
)


def verify_package_topology() -> None:
    missing: list[str] = []

    for package_name in EXPECTED_PACKAGES:
        package_path = COGNITION_ROOT.joinpath(
            *package_name.split(".")
        )
        if not package_path.is_dir():
            missing.append(
                f"directory: core/cognition/{package_name}"
            )

        if not (package_path / "__init__.py").is_file():
            missing.append(
                f"package marker: "
                f"core/cognition/{package_name}/__init__.py"
            )

    if missing:
        raise AssertionError(
            "Missing permanent cognition topology: "
            + ", ".join(missing)
        )


def verify_placeholder_package_imports() -> None:
    violations: list[str] = []

    for package_name in EXPECTED_PACKAGES:
        module = importlib.import_module(
            f"core.cognition.{package_name}"
        )

        if not hasattr(module, "__all__"):
            violations.append(
                f"{package_name} does not define __all__"
            )
            continue

        if tuple(module.__all__) != ():
            violations.append(
                f"{package_name} exposes premature public symbols: "
                f"{tuple(module.__all__)!r}"
            )

    if violations:
        raise AssertionError("; ".join(violations))


def verify_existing_modules_remain_in_place() -> None:
    missing = [
        module_name
        for module_name in EXISTING_PRODUCTION_MODULES
        if not (COGNITION_ROOT / module_name).is_file()
    ]

    if missing:
        raise AssertionError(
            "Package A must not move production modules. Missing: "
            + ", ".join(missing)
        )


def verify_existing_public_api() -> None:
    cognition = importlib.import_module("core.cognition")

    if not hasattr(cognition, "__all__"):
        raise AssertionError(
            "core.cognition no longer defines __all__."
        )

    if not tuple(cognition.__all__):
        raise AssertionError(
            "core.cognition public API is unexpectedly empty."
        )

    missing = [
        export_name
        for export_name in REQUIRED_PUBLIC_EXPORTS
        if not hasattr(cognition, export_name)
    ]

    if missing:
        raise AssertionError(
            "Missing representative public exports: "
            + ", ".join(missing)
        )


def verify_documentation() -> None:
    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in REQUIRED_DOCUMENTS
        if not path.is_file()
    ]

    if missing:
        raise AssertionError(
            "Missing R0-A documentation: "
            + ", ".join(missing)
        )


def verify_compilation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(COGNITION_ROOT),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise AssertionError(
            "Cognition package compilation failed."
        )


def verify_package_a_tests() -> None:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(PROJECT_ROOT / "tests/cognition"),
        pattern="test_genesis_4r0a_repository_skeleton.py",
        top_level_dir=str(PROJECT_ROOT),
    )

    result = unittest.TextTestRunner(
        verbosity=1,
    ).run(suite)

    if not result.wasSuccessful():
        raise AssertionError(
            "Genesis IV-R0 Package A tests failed."
        )


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))

    checks: tuple[tuple[str, Callable[[], None]], ...] = (
        ("Permanent package topology", verify_package_topology),
        (
            "Placeholder package imports",
            verify_placeholder_package_imports,
        ),
        (
            "Existing production modules retained",
            verify_existing_modules_remain_in_place,
        ),
        ("Existing cognition public API", verify_existing_public_api),
        ("Architecture documentation", verify_documentation),
        ("Cognition package compilation", verify_compilation),
        ("Genesis IV-R0-A unit tests", verify_package_a_tests),
    )

    failures = 0

    print()
    print("=" * 70)
    print(
        "JARVIS GENESIS IV-R0-A — "
        "COGNITION REPOSITORY SKELETON"
    )
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
    print(f"Checks executed: {len(checks)}")
    print(f"Checks failed  : {failures}")
    print(
        "Overall status : "
        + ("EXCELLENT" if failures == 0 else "FAILED")
    )
    print("=" * 70)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

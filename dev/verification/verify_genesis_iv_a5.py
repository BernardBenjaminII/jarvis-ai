#!/usr/bin/env python3
"""Certification for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

import ast
import hashlib
import json
import py_compile
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "core/cognition/reasoner/__init__.py",
    "core/cognition/reasoner/contracts.py",
    "core/cognition/reasoner/enums.py",
    "core/cognition/reasoner/errors.py",
    "core/cognition/reasoner/models.py",
    "core/cognition/reasoner/engine.py",
    "core/cognition/reasoner/repository.py",
    "core/cognition/reasoner/service.py",
    "tests/test_genesis_iv_a5_executive_reasoner.py",
    "docs/architecture/genesis_iv_a5_executive_reasoner.md",
    "docs/decisions/ADR-0030-executive-reasoning-policy.md",
    "dev/verification/verify_genesis_iv_a5.py",
    "dev/verify_genesis_4a5.sh",
)

PACKAGE_FILES = tuple(
    item
    for item in REQUIRED_FILES
    if item.startswith("core/") and item.endswith(".py")
)

EXPECTED_EXPORTS = (
    "DeterministicExecutiveReasoner",
    "ExecutiveReasoner",
    "ExecutiveReasoningError",
    "ExecutiveReasoningResult",
    "ExecutiveReasoningService",
    "HypothesisRanking",
    "InMemoryReasoningRepository",
    "InvalidReasoningInputError",
    "InvalidReasoningResultError",
    "ReasoningDisposition",
    "ReasoningPolicy",
    "ReasoningQuery",
    "ReasoningRepository",
    "ReasoningRepositoryClosedError",
    "ReasoningRepositoryDisposition",
    "ReasoningResultNotFoundError",
    "ReasoningStatus",
    "derive_reasoning_identity",
)

FORBIDDEN_PREFIXES = (
    "core.cognition.decision",
    "core.decision",
    "core.execution",
)


class VerificationFailure(RuntimeError):
    """Certification failure."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def passed(label: str) -> None:
    print(f"[PASS] {label}")


def verify_files() -> None:
    missing = [
        item
        for item in REQUIRED_FILES
        if not (PROJECT_ROOT / item).is_file()
    ]
    require(not missing, f"missing required files: {missing}")
    passed("Canonical IV-A5 file set")


def verify_prerequisite() -> None:
    import core.cognition.evidence_correlation as evidence_correlation
    import core.cognition.hypothesis as hypothesis
    import core.cognition.situation as situation

    checks = (
        (situation, ("SituationSnapshot",), "Genesis IV-A2"),
        (hypothesis, ("Hypothesis",), "Genesis IV-A3"),
        (
            evidence_correlation,
            ("HypothesisAssessment",),
            "Genesis IV-A4",
        ),
    )
    for module, names, label in checks:
        missing = [name for name in names if not hasattr(module, name)]
        require(not missing, f"{label} prerequisite symbols missing: {missing}")
    passed("Genesis IV-A2/A3/A4 prerequisite compatibility")


def verify_compilation() -> None:
    for item in PACKAGE_FILES + (
        "tests/test_genesis_iv_a5_executive_reasoner.py",
        "dev/verification/verify_genesis_iv_a5.py",
    ):
        py_compile.compile(str(PROJECT_ROOT / item), doraise=True)
    passed("Python compilation")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def verify_dependency_boundary() -> None:
    violations: list[str] = []
    for item in PACKAGE_FILES:
        for module in imported_modules(PROJECT_ROOT / item):
            if module.startswith(FORBIDDEN_PREFIXES):
                violations.append(f"{item}: {module}")
    require(not violations, f"forward dependency violations: {violations}")
    passed("Forward-only cognition dependency boundary")


def verify_public_api() -> None:
    import core.cognition.reasoner as reasoner

    require(
        tuple(reasoner.__all__) == EXPECTED_EXPORTS,
        "public API differs from certified export sequence",
    )
    for name in EXPECTED_EXPORTS:
        require(hasattr(reasoner, name), f"missing public symbol: {name}")
    passed("Stable public reasoner API")


def verify_unit_tests() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_iv_a5_executive_reasoner",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    require(result.returncode == 0, "Genesis IV-A5 unit tests failed")
    passed("Genesis IV-A5 unit tests")


def verify_manifest() -> None:
    manifest = PROJECT_ROOT / "dev/verification/manifests/genesis.manifest"
    if not manifest.exists():
        passed("Genesis manifest not present; registration deferred")
        return

    entries = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    require(
        "dev/verify_genesis_4a5.sh" in entries,
        "Genesis IV-A5 is absent from manifest",
    )
    if "dev/verify_genesis_4a4.sh" in entries:
        require(
            entries.index("dev/verify_genesis_4a4.sh")
            < entries.index("dev/verify_genesis_4a5.sh"),
            "Genesis IV-A5 must follow Genesis IV-A4",
        )
    passed("Constitutional Genesis manifest registration")


def architecture_fingerprint() -> str:
    digest = hashlib.sha256()
    for item in sorted(PACKAGE_FILES):
        digest.update(item.encode("utf-8"))
        digest.update(b"\0")
        digest.update((PROJECT_ROOT / item).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    print("=" * 72)
    print("JARVIS — GENESIS IV-A5 EXECUTIVE REASONER")
    print("=" * 72)

    checks = (
        verify_files,
        verify_prerequisite,
        verify_compilation,
        verify_dependency_boundary,
        verify_public_api,
        verify_unit_tests,
        verify_manifest,
    )

    failures: list[str] = []
    for check in checks:
        try:
            check()
        except Exception as exc:
            failures.append(f"{check.__name__}: {exc}")
            print(f"[FAIL] {check.__name__}: {exc}")

    print(f"[INFO] Architecture fingerprint: {architecture_fingerprint()}")
    print("-" * 72)
    print(f"Checks failed : {len(failures)}")
    print("Overall status: " + ("EXCELLENT" if not failures else "FAILED"))
    print("=" * 72)

    if failures:
        print(json.dumps({"failures": failures}, indent=2, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

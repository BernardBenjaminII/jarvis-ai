#!/usr/bin/env python3
"""Certification for Genesis IV-A4 Executive Evidence Correlation Engine."""

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
    "core/cognition/evidence_correlation/__init__.py",
    "core/cognition/evidence_correlation/contracts.py",
    "core/cognition/evidence_correlation/enums.py",
    "core/cognition/evidence_correlation/errors.py",
    "core/cognition/evidence_correlation/models.py",
    "core/cognition/evidence_correlation/correlator.py",
    "core/cognition/evidence_correlation/repository.py",
    "core/cognition/evidence_correlation/service.py",
    "tests/test_genesis_iv_a4_executive_evidence_correlation.py",
    "docs/architecture/genesis_iv_a4_executive_evidence_correlation.md",
    "docs/decisions/ADR-0029-evidence-correlation-boundary.md",
    "dev/verification/verify_genesis_iv_a4.py",
    "dev/verify_genesis_4a4.sh",
)

PACKAGE_FILES = tuple(
    item
    for item in REQUIRED_FILES
    if item.startswith("core/") and item.endswith(".py")
)

EXPECTED_EXPORTS = (
    "AssessmentDisposition",
    "AssessmentNotFoundError",
    "AssessmentQuery",
    "AssessmentRepository",
    "AssessmentRepositoryClosedError",
    "AssessmentStatus",
    "EvidenceCorrelator",
    "EvidenceCorrelationError",
    "EvidenceLink",
    "EvidencePolarity",
    "EvidenceStrength",
    "ExecutiveEvidenceCorrelator",
    "ExecutiveEvidenceService",
    "HypothesisAssessment",
    "HypothesisCompatibilityError",
    "InMemoryAssessmentRepository",
    "InvalidAssessmentError",
    "InvalidEvidenceLinkError",
    "SituationCompatibilityError",
    "derive_assessment_identity",
)

FORBIDDEN_PREFIXES = (
    "core.cognition.reasoning",
    "core.cognition.decision",
    "core.decision",
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
    passed("Canonical IV-A4 file set")


def verify_prerequisite() -> None:
    import core.cognition.hypothesis as hypothesis
    import core.cognition.situation as situation

    required_hypothesis = ("Hypothesis", "ExecutiveHypothesisGenerator")
    required_situation = ("SituationSnapshot",)

    missing_hypothesis = [
        name for name in required_hypothesis
        if not hasattr(hypothesis, name)
    ]
    missing_situation = [
        name for name in required_situation
        if not hasattr(situation, name)
    ]

    require(
        not missing_hypothesis,
        f"Genesis IV-A3 prerequisite symbols missing: {missing_hypothesis}",
    )
    require(
        not missing_situation,
        f"Genesis IV-A2 prerequisite symbols missing: {missing_situation}",
    )
    passed("Genesis IV-A2/A3 prerequisite compatibility")


def verify_compilation() -> None:
    for item in PACKAGE_FILES + (
        "tests/test_genesis_iv_a4_executive_evidence_correlation.py",
        "dev/verification/verify_genesis_iv_a4.py",
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
    import core.cognition.evidence_correlation as evidence_correlation

    require(
        tuple(evidence_correlation.__all__) == EXPECTED_EXPORTS,
        "public API differs from certified export sequence",
    )
    for name in EXPECTED_EXPORTS:
        require(
            hasattr(evidence_correlation, name),
            f"missing public symbol: {name}",
        )
    passed("Stable public evidence-correlation API")


def verify_unit_tests() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_iv_a4_executive_evidence_correlation",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    require(result.returncode == 0, "Genesis IV-A4 unit tests failed")
    passed("Genesis IV-A4 unit tests")


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
        "dev/verify_genesis_4a4.sh" in entries,
        "Genesis IV-A4 is absent from manifest",
    )
    if "dev/verify_genesis_4a3.sh" in entries:
        require(
            entries.index("dev/verify_genesis_4a3.sh")
            < entries.index("dev/verify_genesis_4a4.sh"),
            "Genesis IV-A4 must follow Genesis IV-A3",
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
    print("JARVIS — GENESIS IV-A4 EXECUTIVE EVIDENCE CORRELATION ENGINE")
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

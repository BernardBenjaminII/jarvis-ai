#!/usr/bin/env python3
"""Certification for Genesis IV-A2 Executive Situation Model."""

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
    "core/cognition/situation/__init__.py",
    "core/cognition/situation/contracts.py",
    "core/cognition/situation/enums.py",
    "core/cognition/situation/errors.py",
    "core/cognition/situation/models.py",
    "core/cognition/situation/projector.py",
    "core/cognition/situation/repository.py",
    "core/cognition/situation/service.py",
    "tests/test_genesis_iv_a2_executive_situation_model.py",
    "docs/architecture/genesis_iv_a2_executive_situation_model.md",
    "docs/decisions/ADR-0027-executive-situation-model.md",
    "dev/verification/verify_genesis_iv_a2.py",
    "dev/verify_genesis_4a2.sh",
)

PACKAGE_FILES = tuple(
    item
    for item in REQUIRED_FILES
    if item.startswith("core/") and item.endswith(".py")
)

EXPECTED_EXPORTS = (
    "ExecutiveSituationProjector",
    "ExecutiveSituationService",
    "InMemorySituationRepository",
    "InvalidSituationError",
    "ObservationCompatibilityError",
    "SituationDisposition",
    "SituationError",
    "SituationNotFoundError",
    "SituationProjector",
    "SituationQuery",
    "SituationRelation",
    "SituationRelationType",
    "SituationRepository",
    "SituationRepositoryClosedError",
    "SituationSnapshot",
    "SituationStatus",
    "derive_situation_confidence",
    "derive_situation_identity",
    "derive_situation_severity",
)

FORBIDDEN_PREFIXES = (
    "core.cognition.hypothesis",
    "core.cognition.evidence",
    "core.reasoning",
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
    passed("Canonical IV-A2 file set")


def verify_prerequisite() -> None:
    import core.cognition.observation as observation

    required = (
        "Observation",
        "ObservationProvenance",
        "ObservationSeverity",
    )
    missing = [name for name in required if not hasattr(observation, name)]
    require(
        not missing,
        f"Genesis IV-A1 prerequisite symbols missing: {missing}",
    )
    passed("Genesis IV-A1 prerequisite compatibility")


def verify_compilation() -> None:
    for item in PACKAGE_FILES + (
        "tests/test_genesis_iv_a2_executive_situation_model.py",
        "dev/verification/verify_genesis_iv_a2.py",
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
    import core.cognition.situation as situation

    require(
        tuple(situation.__all__) == EXPECTED_EXPORTS,
        "public API differs from certified export sequence",
    )
    for name in EXPECTED_EXPORTS:
        require(hasattr(situation, name), f"missing public symbol: {name}")
    passed("Stable public situation API")


def verify_unit_tests() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_iv_a2_executive_situation_model",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    require(result.returncode == 0, "Genesis IV-A2 unit tests failed")
    passed("Genesis IV-A2 unit tests")


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
        "dev/verify_genesis_4a2.sh" in entries,
        "Genesis IV-A2 is absent from manifest",
    )
    if "dev/verify_genesis_4a1.sh" in entries:
        require(
            entries.index("dev/verify_genesis_4a1.sh")
            < entries.index("dev/verify_genesis_4a2.sh"),
            "Genesis IV-A2 must follow Genesis IV-A1",
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
    print("JARVIS — GENESIS IV-A2 EXECUTIVE SITUATION MODEL")
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

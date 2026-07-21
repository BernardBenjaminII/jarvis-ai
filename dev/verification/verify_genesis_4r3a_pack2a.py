#!/usr/bin/env python3
"""Structural and behavioral verification for Genesis IV-R3A Pack 2A."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PACKAGE_ROOT = PROJECT_ROOT / "core" / "evidence"
CONTRACTS_FILE = PACKAGE_ROOT / "contracts.py"

REQUIRED_FILES = (
    CONTRACTS_FILE,
    PACKAGE_ROOT / "__init__.py",
    PROJECT_ROOT / "tests" / "test_genesis_4r3a_pack2a_contracts.py",
    PROJECT_ROOT / "dev" / "verification" / "verify_genesis_4r3a_pack2a.py",
    PROJECT_ROOT / "dev" / "verify_genesis_4r3a_pack2a.sh",
)

REQUIRED_EXPORTS = (
    "Proposition",
    "WeightBreakdown",
    "AdmissibilityDecision",
    "EvidenceAssessment",
    "EvidenceRecord",
    "EvidenceRelationship",
    "EvidenceGap",
    "EvidenceSet",
    "SerializableContract",
)


def run_check(label: str, operation) -> bool:
    try:
        operation()
    except Exception as exc:
        print(f"[FAIL] {label}")
        print(f"       {type(exc).__name__}: {exc}")
        return False

    print(f"[PASS] {label}")
    return True


def verify_required_files() -> None:
    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in REQUIRED_FILES
        if not path.is_file()
    ]
    if missing:
        raise AssertionError(f"Missing required files: {missing}")


def verify_compilation() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            *(str(path) for path in REQUIRED_FILES if path.suffix == ".py"),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def verify_public_imports() -> None:
    module = importlib.import_module("core.evidence")
    missing = [symbol for symbol in REQUIRED_EXPORTS if not hasattr(module, symbol)]
    if missing:
        raise AssertionError(f"Missing public exports: {missing}")


def verify_no_asdict_usage() -> None:
    source = CONTRACTS_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "asdict":
            forbidden.append(node.lineno)
        if isinstance(node, ast.Attribute) and node.attr == "asdict":
            forbidden.append(node.lineno)

    if forbidden:
        raise AssertionError(f"Forbidden dataclasses.asdict usage at lines: {forbidden}")


def verify_contract_scope() -> None:
    forbidden_names = (
        "EvidenceService",
        "EvidenceRegistry",
        "AdmissibilityEngine",
        "EvidenceAggregator",
        "EvidenceWeightingEngine",
    )
    source = CONTRACTS_FILE.read_text(encoding="utf-8")
    unexpected = [name for name in forbidden_names if f"class {name}" in source]
    if unexpected:
        raise AssertionError(f"Premature runtime components found: {unexpected}")


def verify_mappingproxy_regression() -> None:
    from core.evidence import (
        EvidenceDirection,
        EvidenceRecord,
        EvidenceStatus,
        WeightBreakdown,
    )

    weight = WeightBreakdown(
        reliability=1.0,
        relevance=1.0,
        directness=1.0,
        integrity=1.0,
        freshness=1.0,
        independence=1.0,
        final_weight=1.0,
        formula_version="verification",
        rationale="Verification fixture.",
    )
    record = EvidenceRecord(
        evidence_id="verify-ev",
        proposition_id="verify-prop",
        observation_id="verify-obs",
        assessment_id="verify-assessment",
        source_id="verify-source",
        direction=EvidenceDirection.SUPPORTS,
        status=EvidenceStatus.ACTIVE,
        weight=weight,
        rationale="Regression verification.",
        provenance={"nested": {"values": [1, 2, 3]}},
    )

    payload = record.as_dict()
    if payload["provenance"]["nested"]["values"] != [1, 2, 3]:
        raise AssertionError("Canonical serializer changed nested metadata.")


def verify_unit_tests() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_genesis_4r3a_pack2a_contracts",
            "-v",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

def verify_pack1_compatibility() -> None:
    """Verify Pack 1 compatibility guarantees remain intact.

    This intentionally does NOT rerun Pack 1 certification tests.
    It validates only the stable public contract that later releases
    are required to preserve.
    """

    module = importlib.import_module("core.evidence")

    #
    # Stable public enums
    #
    required_enums = (
        "EvidenceDirection",
        "EvidenceStatus",
        "AdmissibilityStatus",
        "AdmissibilityReason",
        "EvidenceRelationshipType",
        "EvidenceGapType",
        "SourceReliabilityClass",
        "EvidenceSufficiencyStatus",
        "PropositionStatus",
        "PropositionModality",
        "AssessmentMethod",
        "IntegrityStatus",
    )

    for name in required_enums:
        if not hasattr(module, name):
            raise AssertionError(f"Missing Pack 1 enum: {name}")

    #
    # Stable error hierarchy
    #
    required_errors = (
        "EvidenceError",
        "EvidenceValidationError",
        "EvidenceIntegrityError",
        "EvidenceConflictError",
        "EvidenceAggregationError",
        "EvidenceRelationshipError",
        "EvidenceSerializationError",
        "EvidenceStateTransitionError",
        "PropositionError",
        "PropositionValidationError",
    )

    for name in required_errors:
        if not hasattr(module, name):
            raise AssertionError(f"Missing Pack 1 error: {name}")

    #
    # Backward-compatible import surface
    #
    public_api = set(module.__all__)

    for name in required_enums + required_errors:
        if name not in public_api:
            raise AssertionError(f"{name} missing from __all__")


def main() -> int:
    print()
    print("=" * 70)
    print("JARVIS GENESIS IV-R3A — PACK 2A DOMAIN CONTRACTS REBUILD")
    print("=" * 70)

    checks = (
        ("Required Pack 2A files", verify_required_files),
        ("Pack 2A Python compilation", verify_compilation),
        ("Stable evidence contract imports", verify_public_imports),
        ("Canonical serializer excludes dataclasses.asdict", verify_no_asdict_usage),
        ("Pack 2A runtime scope boundary", verify_contract_scope),
        ("MappingProxy serialization regression", verify_mappingproxy_regression),
        ("Pack 2A unit tests", verify_unit_tests),
        ("Pack 1 compatibility", verify_pack1_compatibility),
    )

    failures = sum(not run_check(label, operation) for label, operation in checks)

    print("-" * 70)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 70)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

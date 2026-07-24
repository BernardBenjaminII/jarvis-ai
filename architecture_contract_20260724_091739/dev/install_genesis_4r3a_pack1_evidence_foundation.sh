#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# JARVIS GENESIS IV-R3A — EVIDENCE CONTRACTS FOUNDATION
# PACK 1: PACKAGE SKELETON, ENUMS, ERRORS, AND VERIFICATION
# ==============================================================================

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

if [[ ! -d "core" ]] || [[ ! -d "dev" ]] || [[ ! -d "tests" ]]; then
    echo "ERROR: Run this installer from the JARVIS repository root."
    echo "Expected directories: core/, dev/, tests/"
    exit 1
fi

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-R3A — PACK 1 INSTALLER"
echo "======================================================================"
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo "======================================================================"
echo

mkdir -p \
    core/evidence \
    dev/verification \
    tests

cat > core/evidence/enums.py <<'PYEOF'
"""Controlled vocabulary for the Genesis IV-R3 Evidence Engine.

Genesis IV-R3A establishes the stable language used by later evidence
construction, assessment, relationship, aggregation, and reasoning layers.

This module intentionally contains no scoring logic, persistence behavior,
observation access, or reasoning behavior.
"""

from __future__ import annotations

from enum import Enum


class StableStringEnum(str, Enum):
    """String enum with predictable display and serialization behavior."""

    def __str__(self) -> str:
        return self.value


class EvidenceDirection(StableStringEnum):
    """How an evidence item bears on a proposition."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    QUALIFIES = "qualifies"
    NEUTRAL = "neutral"
    UNRESOLVED = "unresolved"


class EvidenceStatus(StableStringEnum):
    """Lifecycle state of an evidence record."""

    PROPOSED = "proposed"
    ADMISSIBILITY_PENDING = "admissibility_pending"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    ASSESSED = "assessed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class AdmissibilityStatus(StableStringEnum):
    """Outcome of an evidence-admissibility evaluation."""

    PENDING = "pending"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


class AdmissibilityReason(StableStringEnum):
    """Canonical reason codes for admissibility outcomes."""

    ACCEPTED = "accepted"
    MISSING_PROVENANCE = "missing_provenance"
    INVALID_PROVENANCE = "invalid_provenance"
    MISSING_OBSERVATION = "missing_observation"
    UNSUPPORTED_OBSERVATION_KIND = "unsupported_observation_kind"
    INVALID_OBSERVATION_STATE = "invalid_observation_state"
    INTEGRITY_CHECK_FAILED = "integrity_check_failed"
    SOURCE_UNRESOLVED = "source_unresolved"
    POLICY_RESTRICTED = "policy_restricted"
    DUPLICATE_SUBMISSION = "duplicate_submission"
    EXPIRED = "expired"
    MALFORMED_PAYLOAD = "malformed_payload"
    TRANSFORMATION_CHAIN_UNRESOLVED = "transformation_chain_unresolved"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    OTHER = "other"


class EvidenceRelationshipType(StableStringEnum):
    """Explicit relationship between two evidence records."""

    CORROBORATES = "corroborates"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    QUALIFIES = "qualifies"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    COMMON_SOURCE = "common_source"


class EvidenceDirectness(StableStringEnum):
    """Distance between an evidence item and the event or state at issue."""

    DIRECT = "direct"
    NEAR_DIRECT = "near_direct"
    INDIRECT = "indirect"
    HEARSAY = "hearsay"
    UNKNOWN = "unknown"


class SourceReliabilityClass(StableStringEnum):
    """Coarse source-reliability classification.

    Numerical weight remains outside the enum. Later phases may map these
    classes to policy-versioned scores while preserving the original class.
    """

    VERIFIED = "verified"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


class EvidenceGapType(StableStringEnum):
    """Known deficiency preventing complete evidentiary evaluation."""

    NO_SUPPORTING_EVIDENCE = "no_supporting_evidence"
    NO_CONTRADICTING_EVIDENCE = "no_contradicting_evidence"
    INSUFFICIENT_INDEPENDENCE = "insufficient_independence"
    INSUFFICIENT_SOURCE_DIVERSITY = "insufficient_source_diversity"
    DIRECT_EVIDENCE_MISSING = "direct_evidence_missing"
    PROVENANCE_INCOMPLETE = "provenance_incomplete"
    INTEGRITY_UNRESOLVED = "integrity_unresolved"
    FRESHNESS_UNRESOLVED = "freshness_unresolved"
    MATERIAL_CONFLICT_UNRESOLVED = "material_conflict_unresolved"
    COVERAGE_INCOMPLETE = "coverage_incomplete"
    POLICY_REQUIREMENT_UNMET = "policy_requirement_unmet"
    OTHER = "other"


class EvidenceSufficiencyStatus(StableStringEnum):
    """Whether an evidence set satisfies its declared sufficiency policy."""

    NOT_ASSESSED = "not_assessed"
    INSUFFICIENT = "insufficient"
    PARTIALLY_SUFFICIENT = "partially_sufficient"
    SUFFICIENT = "sufficient"
    CONFLICTED = "conflicted"


class PropositionStatus(StableStringEnum):
    """Lifecycle state of a proposition."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class PropositionModality(StableStringEnum):
    """Logical character of a proposition."""

    ASSERTION = "assertion"
    POSSIBILITY = "possibility"
    PROBABILITY = "probability"
    NECESSITY = "necessity"
    PREDICTION = "prediction"


class AssessmentMethod(StableStringEnum):
    """Method by which an evidence assessment was produced."""

    DETERMINISTIC_RULE = "deterministic_rule"
    HUMAN_REVIEW = "human_review"
    MODEL_ASSISTED = "model_assisted"
    HYBRID = "hybrid"
    IMPORTED = "imported"


class IntegrityStatus(StableStringEnum):
    """Integrity state of evidence or its source material."""

    NOT_CHECKED = "not_checked"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    UNKNOWN = "unknown"


__all__ = [
    "AdmissibilityReason",
    "AdmissibilityStatus",
    "AssessmentMethod",
    "EvidenceDirection",
    "EvidenceDirectness",
    "EvidenceGapType",
    "EvidenceRelationshipType",
    "EvidenceStatus",
    "EvidenceSufficiencyStatus",
    "IntegrityStatus",
    "PropositionModality",
    "PropositionStatus",
    "SourceReliabilityClass",
    "StableStringEnum",
]
PYEOF

cat > core/evidence/errors.py <<'PYEOF'
"""Typed failures for the Genesis IV-R3 Evidence Engine."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any


class EvidenceError(Exception):
    """Base class for all Evidence Engine domain failures."""

    default_code = "evidence_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Evidence error message must not be empty.")

        self.code = (code or self.default_code).strip()
        if not self.code:
            raise ValueError("Evidence error code must not be empty.")

        self.context = MappingProxyType(dict(context or {}))
        super().__init__(normalized_message)

    def as_dict(self) -> dict[str, Any]:
        """Return a serialization-safe diagnostic representation."""

        return {
            "error_type": type(self).__name__,
            "code": self.code,
            "message": str(self),
            "context": dict(self.context),
        }


class EvidenceValidationError(EvidenceError):
    """Evidence-domain data failed deterministic validation."""

    default_code = "evidence_validation_error"


class EvidenceAdmissibilityError(EvidenceError):
    """An admissibility operation could not be completed."""

    default_code = "evidence_admissibility_error"


class EvidenceConstructionError(EvidenceError):
    """An evidence record could not be constructed."""

    default_code = "evidence_construction_error"


class EvidenceIntegrityError(EvidenceError):
    """Evidence integrity or provenance verification failed."""

    default_code = "evidence_integrity_error"


class EvidenceConflictError(EvidenceError):
    """Evidence relationships contain an invalid or unresolved conflict."""

    default_code = "evidence_conflict_error"


class EvidenceRelationshipError(EvidenceError):
    """An evidence relationship is malformed or prohibited."""

    default_code = "evidence_relationship_error"


class EvidenceAggregationError(EvidenceError):
    """Evidence records could not be aggregated safely."""

    default_code = "evidence_aggregation_error"


class EvidenceFingerprintError(EvidenceError):
    """A deterministic evidence identity could not be produced or verified."""

    default_code = "evidence_fingerprint_error"


class EvidenceSerializationError(EvidenceError):
    """Evidence-domain data could not be serialized or reconstructed."""

    default_code = "evidence_serialization_error"


class EvidenceStateTransitionError(EvidenceError):
    """A requested evidence lifecycle transition is not permitted."""

    default_code = "evidence_state_transition_error"


class PropositionError(EvidenceError):
    """Base class for proposition-related failures."""

    default_code = "proposition_error"


class PropositionValidationError(PropositionError):
    """A proposition failed deterministic validation."""

    default_code = "proposition_validation_error"


class PropositionNotFoundError(PropositionError):
    """A requested proposition does not exist."""

    default_code = "proposition_not_found"


class EvidenceNotFoundError(EvidenceError):
    """A requested evidence record does not exist."""

    default_code = "evidence_not_found"


class ObservationReferenceError(EvidenceError):
    """An evidence record references an invalid observation."""

    default_code = "observation_reference_error"


class UnsupportedObservationError(ObservationReferenceError):
    """An observation cannot participate in the evidence workflow."""

    default_code = "unsupported_observation"


class EvidencePolicyError(EvidenceError):
    """An evidence policy is invalid, missing, or cannot be applied."""

    default_code = "evidence_policy_error"


__all__ = [
    "EvidenceAdmissibilityError",
    "EvidenceAggregationError",
    "EvidenceConflictError",
    "EvidenceConstructionError",
    "EvidenceError",
    "EvidenceFingerprintError",
    "EvidenceIntegrityError",
    "EvidenceNotFoundError",
    "EvidencePolicyError",
    "EvidenceRelationshipError",
    "EvidenceSerializationError",
    "EvidenceStateTransitionError",
    "EvidenceValidationError",
    "ObservationReferenceError",
    "PropositionError",
    "PropositionNotFoundError",
    "PropositionValidationError",
    "UnsupportedObservationError",
]
PYEOF

cat > core/evidence/__init__.py <<'PYEOF'
"""Public API for the JARVIS Genesis IV-R3 Evidence Engine.

Pack 1 exposes only controlled vocabulary and typed failures. Domain contracts,
fingerprinting, validation, and service behavior are introduced in later R3A
packs without weakening this initial boundary.
"""

from .enums import (
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceDirection,
    EvidenceDirectness,
    EvidenceGapType,
    EvidenceRelationshipType,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
    StableStringEnum,
)
from .errors import (
    EvidenceAdmissibilityError,
    EvidenceAggregationError,
    EvidenceConflictError,
    EvidenceConstructionError,
    EvidenceError,
    EvidenceFingerprintError,
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidencePolicyError,
    EvidenceRelationshipError,
    EvidenceSerializationError,
    EvidenceStateTransitionError,
    EvidenceValidationError,
    ObservationReferenceError,
    PropositionError,
    PropositionNotFoundError,
    PropositionValidationError,
    UnsupportedObservationError,
)

__all__ = [
    "AdmissibilityReason",
    "AdmissibilityStatus",
    "AssessmentMethod",
    "EvidenceAdmissibilityError",
    "EvidenceAggregationError",
    "EvidenceConflictError",
    "EvidenceConstructionError",
    "EvidenceDirection",
    "EvidenceDirectness",
    "EvidenceError",
    "EvidenceFingerprintError",
    "EvidenceGapType",
    "EvidenceIntegrityError",
    "EvidenceNotFoundError",
    "EvidencePolicyError",
    "EvidenceRelationshipError",
    "EvidenceRelationshipType",
    "EvidenceSerializationError",
    "EvidenceStateTransitionError",
    "EvidenceStatus",
    "EvidenceSufficiencyStatus",
    "EvidenceValidationError",
    "IntegrityStatus",
    "ObservationReferenceError",
    "PropositionError",
    "PropositionModality",
    "PropositionNotFoundError",
    "PropositionStatus",
    "PropositionValidationError",
    "SourceReliabilityClass",
    "StableStringEnum",
    "UnsupportedObservationError",
]
PYEOF

cat > tests/test_genesis_4r3a_pack1_evidence_foundation.py <<'PYEOF'
"""Tests for Genesis IV-R3A Pack 1."""

from __future__ import annotations

import unittest
from enum import Enum
from types import MappingProxyType

import core.evidence as evidence
from core.evidence.enums import (
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceDirection,
    EvidenceDirectness,
    EvidenceGapType,
    EvidenceRelationshipType,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
    StableStringEnum,
)
from core.evidence.errors import (
    EvidenceAdmissibilityError,
    EvidenceAggregationError,
    EvidenceConflictError,
    EvidenceConstructionError,
    EvidenceError,
    EvidenceFingerprintError,
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidencePolicyError,
    EvidenceRelationshipError,
    EvidenceSerializationError,
    EvidenceStateTransitionError,
    EvidenceValidationError,
    ObservationReferenceError,
    PropositionError,
    PropositionNotFoundError,
    PropositionValidationError,
    UnsupportedObservationError,
)


class EvidenceEnumTests(unittest.TestCase):
    def test_all_public_enums_are_string_enums(self) -> None:
        enum_types = (
            AdmissibilityReason,
            AdmissibilityStatus,
            AssessmentMethod,
            EvidenceDirection,
            EvidenceDirectness,
            EvidenceGapType,
            EvidenceRelationshipType,
            EvidenceStatus,
            EvidenceSufficiencyStatus,
            IntegrityStatus,
            PropositionModality,
            PropositionStatus,
            SourceReliabilityClass,
        )

        for enum_type in enum_types:
            with self.subTest(enum_type=enum_type.__name__):
                self.assertTrue(issubclass(enum_type, StableStringEnum))
                self.assertTrue(issubclass(enum_type, str))
                self.assertTrue(issubclass(enum_type, Enum))

    def test_enum_string_conversion_returns_wire_value(self) -> None:
        self.assertEqual(str(EvidenceDirection.SUPPORTS), "supports")
        self.assertEqual(
            str(EvidenceRelationshipType.COMMON_SOURCE),
            "common_source",
        )
        self.assertEqual(
            str(AdmissibilityReason.MISSING_PROVENANCE),
            "missing_provenance",
        )

    def test_enum_values_are_unique_within_each_enum(self) -> None:
        enum_types = (
            AdmissibilityReason,
            AdmissibilityStatus,
            AssessmentMethod,
            EvidenceDirection,
            EvidenceDirectness,
            EvidenceGapType,
            EvidenceRelationshipType,
            EvidenceStatus,
            EvidenceSufficiencyStatus,
            IntegrityStatus,
            PropositionModality,
            PropositionStatus,
            SourceReliabilityClass,
        )

        for enum_type in enum_types:
            with self.subTest(enum_type=enum_type.__name__):
                values = [member.value for member in enum_type]
                self.assertEqual(len(values), len(set(values)))


class EvidenceErrorTests(unittest.TestCase):
    def test_error_hierarchy_uses_single_domain_root(self) -> None:
        error_types = (
            EvidenceAdmissibilityError,
            EvidenceAggregationError,
            EvidenceConflictError,
            EvidenceConstructionError,
            EvidenceFingerprintError,
            EvidenceIntegrityError,
            EvidenceNotFoundError,
            EvidencePolicyError,
            EvidenceRelationshipError,
            EvidenceSerializationError,
            EvidenceStateTransitionError,
            EvidenceValidationError,
            ObservationReferenceError,
            PropositionError,
            PropositionNotFoundError,
            PropositionValidationError,
            UnsupportedObservationError,
        )

        for error_type in error_types:
            with self.subTest(error_type=error_type.__name__):
                self.assertTrue(issubclass(error_type, EvidenceError))

    def test_error_preserves_immutable_context(self) -> None:
        error = EvidenceValidationError(
            "Invalid evidence score.",
            context={"field": "relevance", "value": 1.4},
        )

        self.assertIsInstance(error.context, MappingProxyType)
        self.assertEqual(error.context["field"], "relevance")
        with self.assertRaises(TypeError):
            error.context["field"] = "integrity"  # type: ignore[index]

    def test_error_serializes_deterministically(self) -> None:
        error = EvidenceIntegrityError(
            "Fingerprint mismatch.",
            code="fingerprint_mismatch",
            context={"evidence_id": "ev_001"},
        )

        self.assertEqual(
            error.as_dict(),
            {
                "error_type": "EvidenceIntegrityError",
                "code": "fingerprint_mismatch",
                "message": "Fingerprint mismatch.",
                "context": {"evidence_id": "ev_001"},
            },
        )

    def test_empty_error_message_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceError("   ")

    def test_empty_error_code_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceError("Failure.", code="   ")


class EvidencePublicApiTests(unittest.TestCase):
    def test_public_api_exports_declared_symbols(self) -> None:
        expected = {
            "AdmissibilityReason",
            "AdmissibilityStatus",
            "AssessmentMethod",
            "EvidenceDirection",
            "EvidenceError",
            "EvidenceRelationshipType",
            "EvidenceStatus",
            "EvidenceValidationError",
            "PropositionNotFoundError",
            "SourceReliabilityClass",
            "UnsupportedObservationError",
        }

        self.assertTrue(expected.issubset(set(evidence.__all__)))
        for symbol in expected:
            with self.subTest(symbol=symbol):
                self.assertTrue(hasattr(evidence, symbol))

    def test_pack1_does_not_export_future_contracts(self) -> None:
        prohibited = {
            "EvidenceRecord",
            "EvidenceSet",
            "EvidenceService",
            "Proposition",
            "WeightBreakdown",
        }

        self.assertTrue(prohibited.isdisjoint(set(evidence.__all__)))


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_4r3a_pack1.py <<'PYEOF'
#!/usr/bin/env python3
"""Structural verification for Genesis IV-R3A Pack 1."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "core" / "evidence"
TEST_FILE = (
    PROJECT_ROOT
    / "tests"
    / "test_genesis_4r3a_pack1_evidence_foundation.py"
)

Check = tuple[str, Callable[[], None]]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_required_files() -> None:
    required = (
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "enums.py",
        PACKAGE_ROOT / "errors.py",
        TEST_FILE,
        PROJECT_ROOT / "dev" / "verify_genesis_4r3a_pack1.sh",
    )
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.is_file()]
    assert_true(not missing, f"Missing required files: {missing}")


def check_python_compilation() -> None:
    files = [
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "enums.py",
        PACKAGE_ROOT / "errors.py",
        TEST_FILE,
        Path(__file__).resolve(),
    ]
    command = [sys.executable, "-m", "py_compile", *(str(path) for path in files)]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def check_importability() -> None:
    module = importlib.import_module("core.evidence")
    assert_true(hasattr(module, "EvidenceDirection"), "EvidenceDirection not exported.")
    assert_true(hasattr(module, "EvidenceError"), "EvidenceError not exported.")


def check_no_reverse_observation_dependency() -> None:
    observation_root = PROJECT_ROOT / "core" / "observation"
    if not observation_root.exists():
        observation_root = PROJECT_ROOT / "core" / "observations"

    if not observation_root.exists():
        return

    violations: list[str] = []
    for path in observation_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue

            if any(
                name == "core.evidence" or name.startswith("core.evidence.")
                for name in names
            ):
                violations.append(str(path.relative_to(PROJECT_ROOT)))

    assert_true(
        not violations,
        "Observation layer must not import Evidence Engine: "
        + ", ".join(sorted(set(violations))),
    )


def check_pack1_scope_boundary() -> None:
    allowed = {"__init__.py", "enums.py", "errors.py"}
    actual = {
        path.name
        for path in PACKAGE_ROOT.glob("*.py")
        if path.name != "__pycache__"
    }

    unexpected = actual - allowed
    assert_true(
        not unexpected,
        "Pack 1 contains future-phase modules: "
        + ", ".join(sorted(unexpected)),
    )


def check_no_runtime_services() -> None:
    prohibited_names = {
        "EvidenceService",
        "EvidenceRecord",
        "EvidenceSet",
        "Proposition",
        "WeightBreakdown",
    }

    discovered: set[str] = set()
    for path in (PACKAGE_ROOT / "__init__.py", PACKAGE_ROOT / "enums.py", PACKAGE_ROOT / "errors.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                discovered.add(node.name)

    overlap = prohibited_names & discovered
    assert_true(
        not overlap,
        f"Pack 1 introduced prohibited future symbols: {sorted(overlap)}",
    )


def check_unit_tests() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_genesis_4r3a_pack1_evidence_foundation",
            "-v",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> int:
    checks: tuple[Check, ...] = (
        ("Required Pack 1 files", check_required_files),
        ("Pack 1 Python compilation", check_python_compilation),
        ("Stable evidence imports", check_importability),
        ("Observation-to-evidence dependency direction", check_no_reverse_observation_dependency),
        ("Pack 1 scope boundary", check_pack1_scope_boundary),
        ("No premature runtime contracts or services", check_no_runtime_services),
        ("Pack 1 unit tests", check_unit_tests),
    )

    failures = 0

    print()
    print("=" * 70)
    print("JARVIS GENESIS IV-R3A — EVIDENCE FOUNDATION PACK 1")
    print("=" * 70)

    for label, check in checks:
        try:
            check()
        except Exception as exc:  # noqa: BLE001 - verifier must report all failures
            failures += 1
            print(f"[FAIL] {label}")
            print(f"       {type(exc).__name__}: {exc}")
        else:
            print(f"[PASS] {label}")

    print("-" * 70)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 70)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_4r3a_pack1.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "Running Genesis IV-R3A Pack 1 verification..."
echo "Python: ${PYTHON_BIN}"
echo

"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack1.py
SHEOF

chmod +x \
    dev/verify_genesis_4r3a_pack1.sh \
    dev/verification/verify_genesis_4r3a_pack1.py

echo
echo "Pack 1 files installed."
echo
echo "Running verification..."
echo

PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_4r3a_pack1.sh

echo
echo "======================================================================"
echo "GENESIS IV-R3A PACK 1 INSTALLED AND VERIFIED"
echo "======================================================================"
echo
echo "Created:"
echo "  core/evidence/__init__.py"
echo "  core/evidence/enums.py"
echo "  core/evidence/errors.py"
echo "  tests/test_genesis_4r3a_pack1_evidence_foundation.py"
echo "  dev/verification/verify_genesis_4r3a_pack1.py"
echo "  dev/verify_genesis_4r3a_pack1.sh"
echo

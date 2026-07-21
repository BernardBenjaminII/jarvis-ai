#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

if [[ ! -d "core/evidence" ]] || [[ ! -f "core/evidence/enums.py" ]] || [[ ! -f "core/evidence/errors.py" ]]; then
    echo "ERROR: Genesis IV-R3A Pack 1 is required before Pack 2A."
    exit 1
fi

mkdir -p dev/verification tests

cat > core/evidence/contracts.py <<'PYEOF'
"""Immutable domain contracts for Genesis IV-R3A Pack 2A."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .enums import (
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceDirection,
    EvidenceGapType,
    EvidenceRelationshipType,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
)
from .errors import EvidenceValidationError, PropositionValidationError

SCHEMA_VERSION = "genesis-iv-r3a.2a"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise EvidenceValidationError(
            f"{field_name} must not be empty.",
            context={"field": field_name},
        )
    return normalized


def _require_score(value: float, field_name: str) -> float:
    numeric = float(value)
    if numeric < 0.0 or numeric > 1.0:
        raise EvidenceValidationError(
            f"{field_name} must be between 0.0 and 1.0.",
            context={"field": field_name, "value": numeric},
        )
    return numeric


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, MappingProxyType):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    return value


@dataclass(frozen=True, slots=True)
class Proposition:
    proposition_id: str
    statement: str
    subject: str
    predicate: str
    object_value: str | None = None
    status: PropositionStatus = PropositionStatus.DRAFT
    modality: PropositionModality = PropositionModality.ASSERTION
    context: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposition_id", _require_text(self.proposition_id, "proposition_id"))
        object.__setattr__(self, "statement", _require_text(self.statement, "statement"))
        object.__setattr__(self, "subject", _require_text(self.subject, "subject"))
        object.__setattr__(self, "predicate", _require_text(self.predicate, "predicate"))
        if self.object_value is not None:
            object.__setattr__(
                self,
                "object_value",
                _require_text(self.object_value, "object_value"),
            )
        object.__setattr__(self, "context", _freeze_mapping(self.context))
        object.__setattr__(self, "schema_version", _require_text(self.schema_version, "schema_version"))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class WeightBreakdown:
    reliability: float
    relevance: float
    directness: float
    integrity: float
    freshness: float
    independence: float
    final_weight: float
    formula_version: str
    rationale: str

    def __post_init__(self) -> None:
        for name in (
            "reliability",
            "relevance",
            "directness",
            "integrity",
            "freshness",
            "independence",
            "final_weight",
        ):
            object.__setattr__(self, name, _require_score(getattr(self, name), name))
        object.__setattr__(
            self,
            "formula_version",
            _require_text(self.formula_version, "formula_version"),
        )
        object.__setattr__(self, "rationale", _require_text(self.rationale, "rationale"))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class AdmissibilityDecision:
    decision_id: str
    observation_id: str
    status: AdmissibilityStatus
    reason: AdmissibilityReason
    rationale: str
    policy_version: str
    assessed_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(self, "observation_id", _require_text(self.observation_id, "observation_id"))
        object.__setattr__(self, "rationale", _require_text(self.rationale, "rationale"))
        object.__setattr__(
            self,
            "policy_version",
            _require_text(self.policy_version, "policy_version"),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    assessment_id: str
    proposition_id: str
    observation_id: str
    direction: EvidenceDirection
    method: AssessmentMethod
    source_reliability: SourceReliabilityClass
    integrity_status: IntegrityStatus
    weight: WeightBreakdown
    rationale: str
    assessed_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("assessment_id", "proposition_id", "observation_id", "rationale"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    proposition_id: str
    observation_id: str
    assessment_id: str
    source_id: str
    direction: EvidenceDirection
    status: EvidenceStatus
    weight: WeightBreakdown
    rationale: str
    provenance: Mapping[str, Any]
    transformation_chain: tuple[Mapping[str, Any], ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "proposition_id",
            "observation_id",
            "assessment_id",
            "source_id",
            "rationale",
            "schema_version",
        ):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(
            self,
            "transformation_chain",
            tuple(_freeze_mapping(item) for item in self.transformation_chain),
        )

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    relationship_id: str
    left_evidence_id: str
    right_evidence_id: str
    relationship_type: EvidenceRelationshipType
    rationale: str
    confidence: float
    method: AssessmentMethod
    created_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "relationship_id",
            "left_evidence_id",
            "right_evidence_id",
            "rationale",
        ):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        if self.left_evidence_id == self.right_evidence_id:
            raise EvidenceValidationError(
                "Evidence relationship endpoints must differ.",
                context={"evidence_id": self.left_evidence_id},
            )
        object.__setattr__(self, "confidence", _require_score(self.confidence, "confidence"))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class EvidenceGap:
    gap_id: str
    proposition_id: str
    gap_type: EvidenceGapType
    description: str
    severity: float
    blocking: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("gap_id", "proposition_id", "description"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        object.__setattr__(self, "severity", _require_score(self.severity, "severity"))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True, slots=True)
class EvidenceSet:
    evidence_set_id: str
    proposition: Proposition
    supporting: tuple[EvidenceRecord, ...] = ()
    contradicting: tuple[EvidenceRecord, ...] = ()
    qualifying: tuple[EvidenceRecord, ...] = ()
    neutral: tuple[EvidenceRecord, ...] = ()
    unresolved: tuple[EvidenceRecord, ...] = ()
    relationships: tuple[EvidenceRelationship, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()
    aggregate_support: float = 0.0
    aggregate_contradiction: float = 0.0
    source_diversity: float = 0.0
    coverage: float = 0.0
    sufficiency_status: EvidenceSufficiencyStatus = EvidenceSufficiencyStatus.NOT_ASSESSED
    generated_at: datetime = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_set_id",
            _require_text(self.evidence_set_id, "evidence_set_id"),
        )
        for name in (
            "aggregate_support",
            "aggregate_contradiction",
            "source_diversity",
            "coverage",
        ):
            object.__setattr__(self, name, _require_score(getattr(self, name), name))
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )

        all_records = (
            self.supporting
            + self.contradicting
            + self.qualifying
            + self.neutral
            + self.unresolved
        )
        mismatched = [
            record.evidence_id
            for record in all_records
            if record.proposition_id != self.proposition.proposition_id
        ]
        if mismatched:
            raise PropositionValidationError(
                "Evidence set contains records for a different proposition.",
                context={"evidence_ids": mismatched},
            )

    def as_dict(self) -> dict[str, Any]:
        return _serialize(self)


__all__ = [
    "SCHEMA_VERSION",
    "AdmissibilityDecision",
    "EvidenceAssessment",
    "EvidenceGap",
    "EvidenceRecord",
    "EvidenceRelationship",
    "EvidenceSet",
    "Proposition",
    "WeightBreakdown",
    "utc_now",
]
PYEOF

cat > core/evidence/__init__.py <<'PYEOF'
"""Public API for the JARVIS Genesis IV-R3 Evidence Engine."""

from .contracts import (
    SCHEMA_VERSION,
    AdmissibilityDecision,
    EvidenceAssessment,
    EvidenceGap,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceSet,
    Proposition,
    WeightBreakdown,
    utc_now,
)
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
    "SCHEMA_VERSION",
    "AdmissibilityDecision",
    "AdmissibilityReason",
    "AdmissibilityStatus",
    "AssessmentMethod",
    "EvidenceAdmissibilityError",
    "EvidenceAggregationError",
    "EvidenceAssessment",
    "EvidenceConflictError",
    "EvidenceConstructionError",
    "EvidenceDirection",
    "EvidenceDirectness",
    "EvidenceError",
    "EvidenceFingerprintError",
    "EvidenceGap",
    "EvidenceGapType",
    "EvidenceIntegrityError",
    "EvidenceNotFoundError",
    "EvidencePolicyError",
    "EvidenceRecord",
    "EvidenceRelationship",
    "EvidenceRelationshipError",
    "EvidenceRelationshipType",
    "EvidenceSerializationError",
    "EvidenceSet",
    "EvidenceStateTransitionError",
    "EvidenceStatus",
    "EvidenceSufficiencyStatus",
    "EvidenceValidationError",
    "IntegrityStatus",
    "ObservationReferenceError",
    "Proposition",
    "PropositionError",
    "PropositionModality",
    "PropositionNotFoundError",
    "PropositionStatus",
    "PropositionValidationError",
    "SourceReliabilityClass",
    "StableStringEnum",
    "UnsupportedObservationError",
    "WeightBreakdown",
    "utc_now",
]
PYEOF

cat > tests/test_genesis_4r3a_pack2a_contracts.py <<'PYEOF'
from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from core.evidence import (
    AdmissibilityDecision,
    AdmissibilityReason,
    AdmissibilityStatus,
    AssessmentMethod,
    EvidenceAssessment,
    EvidenceDirection,
    EvidenceGap,
    EvidenceGapType,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipType,
    EvidenceSet,
    EvidenceStatus,
    EvidenceSufficiencyStatus,
    IntegrityStatus,
    Proposition,
    PropositionModality,
    PropositionStatus,
    SourceReliabilityClass,
    WeightBreakdown,
)
from core.evidence.errors import EvidenceValidationError, PropositionValidationError


class EvidenceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposition = Proposition(
            proposition_id="prop-001",
            statement="Pump HP-02 produced pressure below threshold.",
            subject="Pump HP-02",
            predicate="produced pressure below threshold",
            status=PropositionStatus.ACTIVE,
            modality=PropositionModality.ASSERTION,
        )
        self.weight = WeightBreakdown(
            reliability=0.9,
            relevance=0.95,
            directness=0.9,
            integrity=1.0,
            freshness=0.8,
            independence=0.85,
            final_weight=0.88,
            formula_version="r3a-test-1",
            rationale="Deterministic fixture.",
        )
        self.record = EvidenceRecord(
            evidence_id="ev-001",
            proposition_id="prop-001",
            observation_id="obs-001",
            assessment_id="assess-001",
            source_id="sensor-a",
            direction=EvidenceDirection.SUPPORTS,
            status=EvidenceStatus.ACTIVE,
            weight=self.weight,
            rationale="Pressure reading supports proposition.",
            provenance={"source": "sensor-a"},
        )

    def test_contracts_are_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            self.proposition.statement = "changed"  # type: ignore[misc]

    def test_mappings_are_immutable(self) -> None:
        with self.assertRaises(TypeError):
            self.record.provenance["source"] = "sensor-b"  # type: ignore[index]

    def test_weight_rejects_out_of_range_score(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            WeightBreakdown(
                reliability=1.1,
                relevance=1.0,
                directness=1.0,
                integrity=1.0,
                freshness=1.0,
                independence=1.0,
                final_weight=1.0,
                formula_version="x",
                rationale="x",
            )

    def test_relationship_rejects_self_reference(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            EvidenceRelationship(
                relationship_id="rel-001",
                left_evidence_id="ev-001",
                right_evidence_id="ev-001",
                relationship_type=EvidenceRelationshipType.DUPLICATES,
                rationale="Invalid self relationship.",
                confidence=1.0,
                method=AssessmentMethod.DETERMINISTIC_RULE,
            )

    def test_evidence_set_rejects_mismatched_proposition(self) -> None:
        foreign = EvidenceRecord(
            evidence_id="ev-foreign",
            proposition_id="prop-999",
            observation_id="obs-999",
            assessment_id="assess-999",
            source_id="source-x",
            direction=EvidenceDirection.SUPPORTS,
            status=EvidenceStatus.ACTIVE,
            weight=self.weight,
            rationale="Foreign record.",
            provenance={"source": "source-x"},
        )
        with self.assertRaises(PropositionValidationError):
            EvidenceSet(
                evidence_set_id="set-001",
                proposition=self.proposition,
                supporting=(foreign,),
            )

    def test_evidence_set_serializes(self) -> None:
        gap = EvidenceGap(
            gap_id="gap-001",
            proposition_id="prop-001",
            gap_type=EvidenceGapType.DIRECT_EVIDENCE_MISSING,
            description="Second direct source required.",
            severity=0.6,
        )
        evidence_set = EvidenceSet(
            evidence_set_id="set-001",
            proposition=self.proposition,
            supporting=(self.record,),
            gaps=(gap,),
            aggregate_support=0.88,
            aggregate_contradiction=0.0,
            source_diversity=0.5,
            coverage=0.7,
            sufficiency_status=EvidenceSufficiencyStatus.PARTIALLY_SUFFICIENT,
        )
        payload = evidence_set.as_dict()
        self.assertEqual(payload["evidence_set_id"], "set-001")
        self.assertEqual(payload["proposition"]["proposition_id"], "prop-001")
        self.assertEqual(payload["supporting"][0]["evidence_id"], "ev-001")

    def test_assessment_and_admissibility_contracts(self) -> None:
        decision = AdmissibilityDecision(
            decision_id="decision-001",
            observation_id="obs-001",
            status=AdmissibilityStatus.ADMITTED,
            reason=AdmissibilityReason.ACCEPTED,
            rationale="Observation passed Pack 2A fixture policy.",
            policy_version="test-policy-1",
        )
        assessment = EvidenceAssessment(
            assessment_id="assess-001",
            proposition_id="prop-001",
            observation_id="obs-001",
            direction=EvidenceDirection.SUPPORTS,
            method=AssessmentMethod.DETERMINISTIC_RULE,
            source_reliability=SourceReliabilityClass.HIGH,
            integrity_status=IntegrityStatus.VERIFIED,
            weight=self.weight,
            rationale="Observation supports proposition.",
        )
        self.assertEqual(decision.as_dict()["status"], "admitted")
        self.assertEqual(assessment.as_dict()["direction"], "supports")


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_4r3a_pack2a.py <<'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED = (
    PROJECT_ROOT / "core/evidence/contracts.py",
    PROJECT_ROOT / "core/evidence/__init__.py",
    PROJECT_ROOT / "tests/test_genesis_4r3a_pack2a_contracts.py",
)

def main() -> int:
    failures = 0
    print()
    print("=" * 70)
    print("JARVIS GENESIS IV-R3A — PACK 2A DOMAIN CONTRACTS")
    print("=" * 70)

    checks = []

    def required_files() -> None:
        missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED if not path.is_file()]
        if missing:
            raise AssertionError(f"Missing required files: {missing}")

    def compile_files() -> None:
        subprocess.run(
            [sys.executable, "-m", "py_compile", *(str(path) for path in REQUIRED)],
            cwd=PROJECT_ROOT,
            check=True,
        )

    def imports() -> None:
        module = importlib.import_module("core.evidence")
        for symbol in (
            "Proposition",
            "WeightBreakdown",
            "AdmissibilityDecision",
            "EvidenceAssessment",
            "EvidenceRecord",
            "EvidenceRelationship",
            "EvidenceGap",
            "EvidenceSet",
        ):
            if not hasattr(module, symbol):
                raise AssertionError(f"Missing public export: {symbol}")

    def unit_tests() -> None:
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

    checks.extend([
        ("Required Pack 2A files", required_files),
        ("Pack 2A Python compilation", compile_files),
        ("Stable evidence contract imports", imports),
        ("Pack 2A unit tests", unit_tests),
    ])

    for label, check in checks:
        try:
            check()
        except Exception as exc:
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

cat > dev/verify_genesis_4r3a_pack2a.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack2a.py
SHEOF

chmod +x \
    dev/verify_genesis_4r3a_pack2a.sh \
    dev/verification/verify_genesis_4r3a_pack2a.py

PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_4r3a_pack2a.sh

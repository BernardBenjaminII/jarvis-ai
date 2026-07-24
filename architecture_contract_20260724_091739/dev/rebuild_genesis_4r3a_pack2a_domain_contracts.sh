#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-R3A — PACK 2A DOMAIN CONTRACTS REBUILD"
echo "======================================================================"

if [[ ! -d "core/evidence" ]] || [[ ! -f "core/evidence/enums.py" ]] || [[ ! -f "core/evidence/errors.py" ]]; then
    echo "[FAIL] Genesis IV-R3A Pack 1 is required."
    exit 1
fi

mkdir -p \
    core/evidence \
    tests \
    dev/verification \
    .migration_backups

BACKUP_DIR=".migration_backups/genesis_4r3a_pack2a_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

for file in \
    core/evidence/contracts.py \
    core/evidence/__init__.py \
    tests/test_genesis_4r3a_pack2a_contracts.py \
    dev/verification/verify_genesis_4r3a_pack2a.py \
    dev/verify_genesis_4r3a_pack2a.sh
do
    if [[ -f "${file}" ]]; then
        mkdir -p "${BACKUP_DIR}/$(dirname "${file}")"
        cp "${file}" "${BACKUP_DIR}/${file}"
    fi
done

cat > core/evidence/contracts.py <<'PYEOF'
"""Immutable evidence-domain contracts for Genesis IV-R3A Pack 2A.

This module defines the stable data model consumed by later admissibility,
weighting, relationship, aggregation, and reasoning layers.

Serialization is intentionally implemented without ``dataclasses.asdict``.
``asdict`` deep-copies values and is incompatible with ``MappingProxyType``,
which is used here to preserve immutable mappings.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

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

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _require_text(value: str, field_name: str) -> str:
    """Normalize and validate a required text field."""

    if not isinstance(value, str):
        raise EvidenceValidationError(
            f"{field_name} must be a string.",
            context={"field": field_name, "type": type(value).__name__},
        )

    normalized = value.strip()
    if not normalized:
        raise EvidenceValidationError(
            f"{field_name} must not be empty.",
            context={"field": field_name},
        )

    return normalized


def _normalize_optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_score(value: float, field_name: str) -> float:
    """Validate a normalized score in the inclusive range 0.0 through 1.0."""

    if isinstance(value, bool):
        raise EvidenceValidationError(
            f"{field_name} must be numeric, not boolean.",
            context={"field": field_name, "value": value},
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(
            f"{field_name} must be numeric.",
            context={"field": field_name, "value": repr(value)},
        ) from exc

    if numeric < 0.0 or numeric > 1.0:
        raise EvidenceValidationError(
            f"{field_name} must be between 0.0 and 1.0.",
            context={"field": field_name, "value": numeric},
        )

    return numeric


def _freeze_value(value: Any) -> Any:
    """Recursively convert mutable containers to immutable equivalents."""

    if isinstance(value, Mapping):
        frozen = {
            _require_text(str(key), "mapping key"): _freeze_value(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)

    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)

    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)

    if isinstance(value, set):
        return tuple(sorted((_freeze_value(item) for item in value), key=repr))

    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    frozen = _freeze_value(value or {})
    if not isinstance(frozen, Mapping):
        raise EvidenceValidationError(
            "Expected mapping-compatible metadata.",
            context={"type": type(value).__name__},
        )
    return frozen


def _canonical_serialize(value: Any) -> JSONValue:
    """Convert supported contract values to deterministic JSON-compatible data.

    Dataclasses are traversed field-by-field. This avoids deep-copy behavior and
    keeps ``MappingProxyType`` compatible with immutable contract serialization.
    Mapping keys are sorted to produce stable output for future fingerprints.
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise EvidenceValidationError(
                "Datetime values must be timezone-aware.",
                context={"value": value.isoformat()},
            )
        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, Enum):
        return _canonical_serialize(value.value)

    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _canonical_serialize(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, Mapping):
        return {
            str(key): _canonical_serialize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }

    if isinstance(value, (tuple, list)):
        return [_canonical_serialize(item) for item in value]

    raise EvidenceValidationError(
        "Unsupported value encountered during canonical serialization.",
        context={"type": type(value).__name__, "value": repr(value)},
    )


class SerializableContract:
    """Shared canonical serialization behavior for evidence contracts."""

    def as_dict(self) -> dict[str, JSONValue]:
        serialized = _canonical_serialize(self)
        if not isinstance(serialized, dict):
            raise EvidenceValidationError(
                "Contract serialization must produce a dictionary.",
                context={"contract": type(self).__name__},
            )
        return serialized


@dataclass(frozen=True, slots=True)
class Proposition(SerializableContract):
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
        object.__setattr__(
            self,
            "proposition_id",
            _require_text(self.proposition_id, "proposition_id"),
        )
        object.__setattr__(self, "statement", _require_text(self.statement, "statement"))
        object.__setattr__(self, "subject", _require_text(self.subject, "subject"))
        object.__setattr__(self, "predicate", _require_text(self.predicate, "predicate"))
        object.__setattr__(
            self,
            "object_value",
            _normalize_optional_text(self.object_value, "object_value"),
        )
        object.__setattr__(self, "context", _freeze_mapping(self.context))
        object.__setattr__(
            self,
            "schema_version",
            _require_text(self.schema_version, "schema_version"),
        )


@dataclass(frozen=True, slots=True)
class WeightBreakdown(SerializableContract):
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


@dataclass(frozen=True, slots=True)
class AdmissibilityDecision(SerializableContract):
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
        object.__setattr__(
            self,
            "observation_id",
            _require_text(self.observation_id, "observation_id"),
        )
        object.__setattr__(self, "rationale", _require_text(self.rationale, "rationale"))
        object.__setattr__(
            self,
            "policy_version",
            _require_text(self.policy_version, "policy_version"),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class EvidenceAssessment(SerializableContract):
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


@dataclass(frozen=True, slots=True)
class EvidenceRecord(SerializableContract):
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


@dataclass(frozen=True, slots=True)
class EvidenceRelationship(SerializableContract):
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

        object.__setattr__(
            self,
            "confidence",
            _require_score(self.confidence, "confidence"),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class EvidenceGap(SerializableContract):
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


@dataclass(frozen=True, slots=True)
class EvidenceSet(SerializableContract):
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

        for collection_name in (
            "supporting",
            "contradicting",
            "qualifying",
            "neutral",
            "unresolved",
            "relationships",
            "gaps",
        ):
            object.__setattr__(self, collection_name, tuple(getattr(self, collection_name)))

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

        mismatched = tuple(
            record.evidence_id
            for record in all_records
            if record.proposition_id != self.proposition.proposition_id
        )
        if mismatched:
            raise PropositionValidationError(
                "Evidence set contains records for a different proposition.",
                context={"evidence_ids": mismatched},
            )

        evidence_ids = tuple(record.evidence_id for record in all_records)
        duplicate_ids = tuple(
            sorted(
                evidence_id
                for evidence_id in set(evidence_ids)
                if evidence_ids.count(evidence_id) > 1
            )
        )
        if duplicate_ids:
            raise EvidenceValidationError(
                "Evidence set contains duplicate evidence records.",
                context={"evidence_ids": duplicate_ids},
            )


__all__ = [
    "SCHEMA_VERSION",
    "AdmissibilityDecision",
    "EvidenceAssessment",
    "EvidenceGap",
    "EvidenceRecord",
    "EvidenceRelationship",
    "EvidenceSet",
    "JSONValue",
    "Proposition",
    "SerializableContract",
    "WeightBreakdown",
    "utc_now",
]
PYEOF

cat > core/evidence/__init__.py <<'PYEOF'
"""Stable public API for the JARVIS Genesis IV-R3 Evidence Engine."""

from .contracts import (
    SCHEMA_VERSION,
    AdmissibilityDecision,
    EvidenceAssessment,
    EvidenceGap,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceSet,
    Proposition,
    SerializableContract,
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
    "SerializableContract",
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
from datetime import datetime, timezone

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


FIXED_TIME = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)


class EvidenceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposition = Proposition(
            proposition_id="prop-001",
            statement="Pump HP-02 produced pressure below threshold.",
            subject="Pump HP-02",
            predicate="produced pressure below threshold",
            status=PropositionStatus.ACTIVE,
            modality=PropositionModality.ASSERTION,
            context={"mission": {"id": "mission-001", "tags": ["pressure", "safety"]}},
            created_at=FIXED_TIME,
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
            provenance={
                "source": "sensor-a",
                "capture": {"sequence": 7, "channels": ["pressure", "temperature"]},
            },
            transformation_chain=(
                {"operation": "unit-normalization", "from": "psi", "to": "kpa"},
            ),
            created_at=FIXED_TIME,
        )

    def test_contracts_are_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            self.proposition.statement = "changed"  # type: ignore[misc]

    def test_nested_mappings_and_lists_are_immutable(self) -> None:
        with self.assertRaises(TypeError):
            self.record.provenance["source"] = "sensor-b"  # type: ignore[index]

        capture = self.record.provenance["capture"]
        with self.assertRaises(TypeError):
            capture["sequence"] = 8  # type: ignore[index]

        self.assertIsInstance(capture["channels"], tuple)  # type: ignore[index]

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

    def test_weight_rejects_boolean_score(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            WeightBreakdown(
                reliability=True,
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
                created_at=FIXED_TIME,
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
            created_at=FIXED_TIME,
        )
        with self.assertRaises(PropositionValidationError):
            EvidenceSet(
                evidence_set_id="set-001",
                proposition=self.proposition,
                supporting=(foreign,),
                generated_at=FIXED_TIME,
            )

    def test_evidence_set_rejects_duplicate_record(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            EvidenceSet(
                evidence_set_id="set-001",
                proposition=self.proposition,
                supporting=(self.record,),
                neutral=(self.record,),
                generated_at=FIXED_TIME,
            )

    def test_mappingproxy_serialization_regression(self) -> None:
        payload = self.record.as_dict()

        self.assertEqual(payload["provenance"]["source"], "sensor-a")
        self.assertEqual(payload["provenance"]["capture"]["sequence"], 7)
        self.assertEqual(
            payload["provenance"]["capture"]["channels"],
            ["pressure", "temperature"],
        )

    def test_serialization_is_deterministic_and_key_ordered(self) -> None:
        first = Proposition(
            proposition_id="prop-order",
            statement="Ordering is deterministic.",
            subject="serializer",
            predicate="orders mappings",
            context={"z": 1, "a": 2, "m": {"y": 3, "b": 4}},
            created_at=FIXED_TIME,
        )
        second = Proposition(
            proposition_id="prop-order",
            statement="Ordering is deterministic.",
            subject="serializer",
            predicate="orders mappings",
            context={"a": 2, "m": {"b": 4, "y": 3}, "z": 1},
            created_at=FIXED_TIME,
        )

        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(list(first.as_dict()["context"].keys()), ["a", "m", "z"])

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
            generated_at=FIXED_TIME,
        )

        payload = evidence_set.as_dict()

        self.assertEqual(payload["evidence_set_id"], "set-001")
        self.assertEqual(payload["proposition"]["proposition_id"], "prop-001")
        self.assertEqual(payload["supporting"][0]["evidence_id"], "ev-001")
        self.assertEqual(payload["generated_at"], "2026-07-21T12:00:00+00:00")

    def test_assessment_and_admissibility_contracts_serialize(self) -> None:
        decision = AdmissibilityDecision(
            decision_id="decision-001",
            observation_id="obs-001",
            status=AdmissibilityStatus.ADMITTED,
            reason=AdmissibilityReason.ACCEPTED,
            rationale="Observation passed Pack 2A fixture policy.",
            policy_version="test-policy-1",
            assessed_at=FIXED_TIME,
            metadata={"review": {"required": False}},
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
            assessed_at=FIXED_TIME,
        )

        self.assertEqual(decision.as_dict()["status"], "admitted")
        self.assertEqual(decision.as_dict()["metadata"]["review"]["required"], False)
        self.assertEqual(assessment.as_dict()["direction"], "supports")


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_4r3a_pack2a.py <<'PYEOF'
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
        ("Pack 1 evidence foundation regression", verify_pack1_regression),
    )

    failures = sum(not run_check(label, operation) for label, operation in checks)

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

echo
echo "Running Genesis IV-R3A Pack 2A verification..."
echo "Python: ${PYTHON_BIN}"
echo

"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack2a.py
SHEOF

chmod +x \
    dev/verify_genesis_4r3a_pack2a.sh \
    dev/verification/verify_genesis_4r3a_pack2a.py

echo "[PASS] Pack 2A replacement files installed"
echo "Backup: ${BACKUP_DIR}"
echo

PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_4r3a_pack2a.sh

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

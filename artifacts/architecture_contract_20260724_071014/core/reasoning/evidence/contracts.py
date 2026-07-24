"""Immutable constitutional contracts for Genesis II-A4 Evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

from .enums import (
    AssessmentMethod,
    ClassificationLevel,
    EvidenceModality,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatus,
    UncertaintyKind,
)
from .errors import (
    EvidenceRelationshipError,
    EvidenceTemporalError,
    EvidenceUncertaintyError,
    EvidenceValidationError,
)
from .identifiers import (
    EvidenceAssessmentId,
    EvidenceContentId,
    EvidenceId,
    EvidenceRelationshipId,
    EvidenceStatusEventId,
)
from .validation import (
    normalize_key_value_pairs,
    normalize_optional_text,
    normalize_string_tuple,
    normalize_text,
    require_nonnegative_integer,
    validate_aware_datetime,
    validate_language_tag,
    validate_media_type,
    validate_nonnegative_decimal,
    validate_unit_decimal,
)


_PLACEHOLDER_DIGEST = "0" * 64


def _placeholder_evidence_id() -> EvidenceId:
    """Return a syntactically valid non-canonical Evidence identifier."""

    return EvidenceId(f"evidence:{_PLACEHOLDER_DIGEST}")


def _placeholder_assessment_id() -> EvidenceAssessmentId:
    """Return a syntactically valid non-canonical assessment identifier."""

    return EvidenceAssessmentId(
        f"evidence-assessment:{_PLACEHOLDER_DIGEST}"
    )


def _placeholder_relationship_id() -> EvidenceRelationshipId:
    """Return a syntactically valid non-canonical relationship identifier."""

    return EvidenceRelationshipId(
        f"evidence-relationship:{_PLACEHOLDER_DIGEST}"
    )


def _placeholder_status_event_id() -> EvidenceStatusEventId:
    """Return a syntactically valid non-canonical status-event identifier."""

    return EvidenceStatusEventId(
        f"evidence-status-event:{_PLACEHOLDER_DIGEST}"
    )


@dataclass(frozen=True, slots=True)
class EvidenceContent:
    """Normalized information-bearing content admitted as Evidence."""

    statement: str
    media_type: str = "text/plain"
    language: str | None = None
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "statement",
            normalize_text(
                self.statement,
                field_name="statement",
            ),
        )
        object.__setattr__(
            self,
            "media_type",
            validate_media_type(self.media_type),
        )
        object.__setattr__(
            self,
            "language",
            validate_language_tag(self.language),
        )
        object.__setattr__(
            self,
            "attributes",
            normalize_key_value_pairs(
                self.attributes,
                field_name="attributes",
            ),
        )

    @property
    def content_id(self) -> EvidenceContentId:
        """Return the deterministic identity of normalized content."""

        return EvidenceContentId.from_payload(self)


@dataclass(frozen=True, slots=True)
class EvidenceOrigin:
    """Origin and source-dependence metadata for Evidence."""

    source_type: EvidenceSourceType
    source_id: str
    immediate_source_id: str | None = None
    origin_id: str | None = None
    source_family_id: str | None = None
    collection_event_id: str | None = None
    dependency_group_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, EvidenceSourceType):
            raise EvidenceValidationError(
                "source_type must be an EvidenceSourceType"
            )

        object.__setattr__(
            self,
            "source_id",
            normalize_text(
                self.source_id,
                field_name="source_id",
            ),
        )
        object.__setattr__(
            self,
            "immediate_source_id",
            normalize_optional_text(
                self.immediate_source_id,
                field_name="immediate_source_id",
            ),
        )
        object.__setattr__(
            self,
            "origin_id",
            normalize_optional_text(
                self.origin_id,
                field_name="origin_id",
            ),
        )
        object.__setattr__(
            self,
            "source_family_id",
            normalize_optional_text(
                self.source_family_id,
                field_name="source_family_id",
            ),
        )
        object.__setattr__(
            self,
            "collection_event_id",
            normalize_optional_text(
                self.collection_event_id,
                field_name="collection_event_id",
            ),
        )
        object.__setattr__(
            self,
            "dependency_group_ids",
            normalize_string_tuple(
                self.dependency_group_ids,
                field_name="dependency_group_ids",
                sort_values=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceProvenanceStep:
    """One immutable transformation or custody step."""

    sequence: int
    actor: str
    mechanism: str
    input_ids: tuple[str, ...] = ()
    transformation: str | None = None
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(
                self.sequence,
                field_name="sequence",
            ),
        )
        object.__setattr__(
            self,
            "actor",
            normalize_text(
                self.actor,
                field_name="actor",
            ),
        )
        object.__setattr__(
            self,
            "mechanism",
            normalize_text(
                self.mechanism,
                field_name="mechanism",
            ),
        )
        object.__setattr__(
            self,
            "input_ids",
            normalize_string_tuple(
                self.input_ids,
                field_name="input_ids",
                sort_values=True,
            ),
        )
        object.__setattr__(
            self,
            "transformation",
            normalize_optional_text(
                self.transformation,
                field_name="transformation",
            ),
        )
        object.__setattr__(
            self,
            "fingerprint",
            normalize_optional_text(
                self.fingerprint,
                field_name="fingerprint",
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Ordered append-safe provenance chain."""

    steps: tuple[EvidenceProvenanceStep, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            object.__setattr__(self, "steps", tuple(self.steps))

        if not self.steps:
            raise EvidenceValidationError(
                "provenance must contain at least one step"
            )

        if not all(
            isinstance(step, EvidenceProvenanceStep)
            for step in self.steps
        ):
            raise EvidenceValidationError(
                "provenance steps must be EvidenceProvenanceStep objects"
            )

        sequences = tuple(step.sequence for step in self.steps)
        expected = tuple(range(len(self.steps)))

        if sequences != expected:
            raise EvidenceValidationError(
                "provenance sequences must be contiguous and begin at zero"
            )


@dataclass(frozen=True, slots=True)
class EvidenceTemporalScope:
    """Temporal metadata independent from Evidence identity creation."""

    recorded_at: datetime
    observed_at: datetime | None = None
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recorded_at",
            validate_aware_datetime(
                self.recorded_at,
                field_name="recorded_at",
                required=True,
            ),
        )

        for field_name in (
            "observed_at",
            "published_at",
            "valid_from",
            "valid_until",
        ):
            object.__setattr__(
                self,
                field_name,
                validate_aware_datetime(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise EvidenceTemporalError(
                "valid_until must not precede valid_from"
            )


@dataclass(frozen=True, slots=True)
class BeliefMass:
    """One focal-set mass in a belief-function representation."""

    focal_set: tuple[str, ...]
    mass: Decimal

    def __post_init__(self) -> None:
        normalized_focal_set = normalize_string_tuple(
            self.focal_set,
            field_name="focal_set",
            sort_values=True,
        )

        if not normalized_focal_set:
            raise EvidenceUncertaintyError(
                "belief focal_set must not be empty"
            )

        object.__setattr__(
            self,
            "focal_set",
            normalized_focal_set,
        )
        object.__setattr__(
            self,
            "mass",
            validate_unit_decimal(
                self.mass,
                field_name="mass",
                required=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceUncertainty:
    """Typed uncertainty representation without a universal calculus."""

    kind: UncertaintyKind
    qualitative_label: str | None = None
    probability: Decimal | None = None
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    likelihood: Decimal | None = None
    belief_masses: tuple[BeliefMass, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, UncertaintyKind):
            raise EvidenceUncertaintyError(
                "kind must be an UncertaintyKind"
            )

        object.__setattr__(
            self,
            "qualitative_label",
            normalize_optional_text(
                self.qualitative_label,
                field_name="qualitative_label",
            ),
        )
        object.__setattr__(
            self,
            "probability",
            validate_unit_decimal(
                self.probability,
                field_name="probability",
            ),
        )
        object.__setattr__(
            self,
            "lower_bound",
            validate_unit_decimal(
                self.lower_bound,
                field_name="lower_bound",
            ),
        )
        object.__setattr__(
            self,
            "upper_bound",
            validate_unit_decimal(
                self.upper_bound,
                field_name="upper_bound",
            ),
        )
        object.__setattr__(
            self,
            "likelihood",
            validate_nonnegative_decimal(
                self.likelihood,
                field_name="likelihood",
            ),
        )

        if not isinstance(self.belief_masses, tuple):
            object.__setattr__(
                self,
                "belief_masses",
                tuple(self.belief_masses),
            )

        if not all(
            isinstance(item, BeliefMass)
            for item in self.belief_masses
        ):
            raise EvidenceUncertaintyError(
                "belief_masses must contain BeliefMass objects"
            )

        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.lower_bound > self.upper_bound
        ):
            raise EvidenceUncertaintyError(
                "lower_bound must not exceed upper_bound"
            )

        self._validate_kind_contract()

    def _validate_kind_contract(self) -> None:
        populated = {
            "qualitative_label": self.qualitative_label is not None,
            "probability": self.probability is not None,
            "interval": (
                self.lower_bound is not None
                or self.upper_bound is not None
            ),
            "likelihood": self.likelihood is not None,
            "belief_masses": bool(self.belief_masses),
        }

        if self.kind is UncertaintyKind.UNKNOWN:
            if any(populated.values()):
                raise EvidenceUncertaintyError(
                    "UNKNOWN uncertainty must not contain quantified values"
                )
            return

        if self.kind is UncertaintyKind.QUALITATIVE:
            if self.qualitative_label is None:
                raise EvidenceUncertaintyError(
                    "QUALITATIVE uncertainty requires qualitative_label"
                )

            if any(
                populated[name]
                for name in (
                    "probability",
                    "interval",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "QUALITATIVE uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.PROBABILITY:
            if self.probability is None:
                raise EvidenceUncertaintyError(
                    "PROBABILITY uncertainty requires probability"
                )

            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "interval",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "PROBABILITY uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.INTERVAL:
            if (
                self.lower_bound is None
                or self.upper_bound is None
            ):
                raise EvidenceUncertaintyError(
                    "INTERVAL uncertainty requires both bounds"
                )

            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "likelihood",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "INTERVAL uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.LIKELIHOOD:
            if self.likelihood is None:
                raise EvidenceUncertaintyError(
                    "LIKELIHOOD uncertainty requires likelihood"
                )

            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "interval",
                    "belief_masses",
                )
            ):
                raise EvidenceUncertaintyError(
                    "LIKELIHOOD uncertainty contains incompatible values"
                )
            return

        if self.kind is UncertaintyKind.BELIEF_FUNCTION:
            if not self.belief_masses:
                raise EvidenceUncertaintyError(
                    "BELIEF_FUNCTION uncertainty requires belief_masses"
                )

            if any(
                populated[name]
                for name in (
                    "qualitative_label",
                    "probability",
                    "interval",
                    "likelihood",
                )
            ):
                raise EvidenceUncertaintyError(
                    "BELIEF_FUNCTION uncertainty contains incompatible values"
                )

            total = sum(
                (
                    belief_mass.mass
                    for belief_mass in self.belief_masses
                ),
                start=Decimal("0"),
            )

            if total != Decimal("1"):
                raise EvidenceUncertaintyError(
                    "belief-function masses must sum exactly to 1"
                )


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    """Typed directional relationship between Evidence records."""

    relationship_id: EvidenceRelationshipId
    source_evidence_id: EvidenceId
    target_evidence_id: EvidenceId
    relationship_type: EvidenceRelationshipType
    rationale: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        if not isinstance(
            self.relationship_id,
            EvidenceRelationshipId,
        ):
            raise EvidenceRelationshipError(
                "relationship_id must be an EvidenceRelationshipId"
            )

        if not isinstance(self.source_evidence_id, EvidenceId):
            raise EvidenceRelationshipError(
                "source_evidence_id must be an EvidenceId"
            )

        if not isinstance(self.target_evidence_id, EvidenceId):
            raise EvidenceRelationshipError(
                "target_evidence_id must be an EvidenceId"
            )

        if self.source_evidence_id == self.target_evidence_id:
            raise EvidenceRelationshipError(
                "an Evidence relationship cannot target itself"
            )

        if not isinstance(
            self.relationship_type,
            EvidenceRelationshipType,
        ):
            raise EvidenceRelationshipError(
                "relationship_type must be an EvidenceRelationshipType"
            )

        object.__setattr__(
            self,
            "rationale",
            normalize_optional_text(
                self.rationale,
                field_name="rationale",
            ),
        )
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(
                self.sequence,
                field_name="sequence",
            ),
        )

    def _identity_payload(self) -> dict[str, Any]:
        """Return the canonical relationship identity payload."""

        return {
            "source_evidence_id": self.source_evidence_id,
            "target_evidence_id": self.target_evidence_id,
            "relationship_type": self.relationship_type,
            "rationale": self.rationale,
            "sequence": self.sequence,
        }

    @classmethod
    def create(
        cls,
        *,
        source_evidence_id: EvidenceId,
        target_evidence_id: EvidenceId,
        relationship_type: EvidenceRelationshipType,
        rationale: str | None = None,
        sequence: int = 0,
    ) -> "EvidenceRelationship":
        """Create a validated, normalized, deterministically identified relationship."""

        provisional = cls(
            relationship_id=_placeholder_relationship_id(),
            source_evidence_id=source_evidence_id,
            target_evidence_id=target_evidence_id,
            relationship_type=relationship_type,
            rationale=rationale,
            sequence=sequence,
        )

        canonical_id = EvidenceRelationshipId.from_payload(
            provisional._identity_payload()
        )

        return replace(
            provisional,
            relationship_id=canonical_id,
        )


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable historical Evidence record."""

    evidence_id: EvidenceId
    content: EvidenceContent
    origin: EvidenceOrigin
    provenance: EvidenceProvenance
    temporal_scope: EvidenceTemporalScope
    uncertainty: EvidenceUncertainty
    modality: EvidenceModality
    status: EvidenceStatus = EvidenceStatus.ACTIVE
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    tags: tuple[str, ...] = ()
    parent_evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )

        if not isinstance(self.content, EvidenceContent):
            raise EvidenceValidationError(
                "content must be an EvidenceContent"
            )

        if not isinstance(self.origin, EvidenceOrigin):
            raise EvidenceValidationError(
                "origin must be an EvidenceOrigin"
            )

        if not isinstance(self.provenance, EvidenceProvenance):
            raise EvidenceValidationError(
                "provenance must be an EvidenceProvenance"
            )

        if not isinstance(
            self.temporal_scope,
            EvidenceTemporalScope,
        ):
            raise EvidenceValidationError(
                "temporal_scope must be an EvidenceTemporalScope"
            )

        if not isinstance(
            self.uncertainty,
            EvidenceUncertainty,
        ):
            raise EvidenceValidationError(
                "uncertainty must be an EvidenceUncertainty"
            )

        if not isinstance(self.modality, EvidenceModality):
            raise EvidenceValidationError(
                "modality must be an EvidenceModality"
            )

        if not isinstance(self.status, EvidenceStatus):
            raise EvidenceValidationError(
                "status must be an EvidenceStatus"
            )

        if not isinstance(
            self.classification,
            ClassificationLevel,
        ):
            raise EvidenceValidationError(
                "classification must be a ClassificationLevel"
            )

        object.__setattr__(
            self,
            "tags",
            normalize_string_tuple(
                self.tags,
                field_name="tags",
                sort_values=True,
            ),
        )

        normalized_parents = tuple(
            sorted(self.parent_evidence_ids)
        )

        if not all(
            isinstance(parent_id, EvidenceId)
            for parent_id in normalized_parents
        ):
            raise EvidenceValidationError(
                "parent_evidence_ids must contain EvidenceId objects"
            )

        if len(set(normalized_parents)) != len(normalized_parents):
            raise EvidenceValidationError(
                "parent_evidence_ids must not contain duplicates"
            )

        if self.evidence_id in normalized_parents:
            raise EvidenceValidationError(
                "Evidence cannot be its own parent"
            )

        object.__setattr__(
            self,
            "parent_evidence_ids",
            normalized_parents,
        )

    def _identity_payload(self) -> dict[str, Any]:
        """Return the canonical Evidence-record identity payload.

        Current standing is intentionally excluded. Standing evolves through
        append-only EvidenceStatusEvent objects rather than record mutation.
        """

        return {
            "content_id": self.content.content_id,
            "origin": self.origin,
            "provenance": self.provenance,
            "temporal_scope": self.temporal_scope,
            "uncertainty": self.uncertainty,
            "modality": self.modality,
            "classification": self.classification,
            "tags": self.tags,
            "parent_evidence_ids": self.parent_evidence_ids,
        }

    @classmethod
    def create(
        cls,
        *,
        content: EvidenceContent,
        origin: EvidenceOrigin,
        provenance: EvidenceProvenance,
        temporal_scope: EvidenceTemporalScope,
        uncertainty: EvidenceUncertainty,
        modality: EvidenceModality,
        status: EvidenceStatus = EvidenceStatus.ACTIVE,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        tags: Iterable[str] = (),
        parent_evidence_ids: Iterable[EvidenceId] = (),
    ) -> "EvidenceRecord":
        """Create a validated, normalized, deterministically identified record."""

        provisional = cls(
            evidence_id=_placeholder_evidence_id(),
            content=content,
            origin=origin,
            provenance=provenance,
            temporal_scope=temporal_scope,
            uncertainty=uncertainty,
            modality=modality,
            status=status,
            classification=classification,
            tags=tuple(tags),
            parent_evidence_ids=tuple(parent_evidence_ids),
        )

        canonical_id = EvidenceId.from_payload(
            provisional._identity_payload()
        )

        return replace(
            provisional,
            evidence_id=canonical_id,
        )


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    """Context-specific evaluation that does not mutate Evidence."""

    assessment_id: EvidenceAssessmentId
    evidence_id: EvidenceId
    reasoning_context_id: str
    assessor_id: str
    method: AssessmentMethod
    sequence: int
    rationale: str
    source_reliability: Decimal | None = None
    content_credibility: Decimal | None = None
    relevance: Decimal | None = None
    freshness: Decimal | None = None
    independence: Decimal | None = None
    diagnosticity: Decimal | None = None
    completeness: Decimal | None = None
    consistency: Decimal | None = None
    decision_impact: Decimal | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.assessment_id,
            EvidenceAssessmentId,
        ):
            raise EvidenceValidationError(
                "assessment_id must be an EvidenceAssessmentId"
            )

        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )

        if not isinstance(self.method, AssessmentMethod):
            raise EvidenceValidationError(
                "method must be an AssessmentMethod"
            )

        object.__setattr__(
            self,
            "reasoning_context_id",
            normalize_text(
                self.reasoning_context_id,
                field_name="reasoning_context_id",
            ),
        )
        object.__setattr__(
            self,
            "assessor_id",
            normalize_text(
                self.assessor_id,
                field_name="assessor_id",
            ),
        )
        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(
                self.sequence,
                field_name="sequence",
            ),
        )
        object.__setattr__(
            self,
            "rationale",
            normalize_text(
                self.rationale,
                field_name="rationale",
            ),
        )

        score_fields = (
            "source_reliability",
            "content_credibility",
            "relevance",
            "freshness",
            "independence",
            "diagnosticity",
            "completeness",
            "consistency",
            "decision_impact",
        )

        for field_name in score_fields:
            object.__setattr__(
                self,
                field_name,
                validate_unit_decimal(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

    def _identity_payload(self) -> dict[str, Any]:
        """Return the canonical assessment identity payload."""

        return {
            "evidence_id": self.evidence_id,
            "reasoning_context_id": self.reasoning_context_id,
            "assessor_id": self.assessor_id,
            "method": self.method,
            "sequence": self.sequence,
            "rationale": self.rationale,
            "source_reliability": self.source_reliability,
            "content_credibility": self.content_credibility,
            "relevance": self.relevance,
            "freshness": self.freshness,
            "independence": self.independence,
            "diagnosticity": self.diagnosticity,
            "completeness": self.completeness,
            "consistency": self.consistency,
            "decision_impact": self.decision_impact,
        }

    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceId,
        reasoning_context_id: str,
        assessor_id: str,
        method: AssessmentMethod,
        sequence: int,
        rationale: str,
        source_reliability: Decimal | int | str | None = None,
        content_credibility: Decimal | int | str | None = None,
        relevance: Decimal | int | str | None = None,
        freshness: Decimal | int | str | None = None,
        independence: Decimal | int | str | None = None,
        diagnosticity: Decimal | int | str | None = None,
        completeness: Decimal | int | str | None = None,
        consistency: Decimal | int | str | None = None,
        decision_impact: Decimal | int | str | None = None,
    ) -> "EvidenceAssessment":
        """Create a validated, normalized, deterministically identified assessment."""

        provisional = cls(
            assessment_id=_placeholder_assessment_id(),
            evidence_id=evidence_id,
            reasoning_context_id=reasoning_context_id,
            assessor_id=assessor_id,
            method=method,
            sequence=sequence,
            rationale=rationale,
            source_reliability=source_reliability,
            content_credibility=content_credibility,
            relevance=relevance,
            freshness=freshness,
            independence=independence,
            diagnosticity=diagnosticity,
            completeness=completeness,
            consistency=consistency,
            decision_impact=decision_impact,
        )

        canonical_id = EvidenceAssessmentId.from_payload(
            provisional._identity_payload()
        )

        return replace(
            provisional,
            assessment_id=canonical_id,
        )


@dataclass(frozen=True, slots=True)
class EvidenceStatusEvent:
    """Append-only event describing a change in Evidence standing."""

    event_id: EvidenceStatusEventId
    evidence_id: EvidenceId
    previous_status: EvidenceStatus
    new_status: EvidenceStatus
    sequence: int
    reason: str
    related_evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.event_id,
            EvidenceStatusEventId,
        ):
            raise EvidenceValidationError(
                "event_id must be an EvidenceStatusEventId"
            )

        if not isinstance(self.evidence_id, EvidenceId):
            raise EvidenceValidationError(
                "evidence_id must be an EvidenceId"
            )

        if not isinstance(
            self.previous_status,
            EvidenceStatus,
        ):
            raise EvidenceValidationError(
                "previous_status must be an EvidenceStatus"
            )

        if not isinstance(self.new_status, EvidenceStatus):
            raise EvidenceValidationError(
                "new_status must be an EvidenceStatus"
            )

        if self.previous_status is self.new_status:
            raise EvidenceValidationError(
                "status event must change Evidence standing"
            )

        object.__setattr__(
            self,
            "sequence",
            require_nonnegative_integer(
                self.sequence,
                field_name="sequence",
            ),
        )
        object.__setattr__(
            self,
            "reason",
            normalize_text(
                self.reason,
                field_name="reason",
            ),
        )

        normalized_related = tuple(
            sorted(self.related_evidence_ids)
        )

        if not all(
            isinstance(item, EvidenceId)
            for item in normalized_related
        ):
            raise EvidenceValidationError(
                "related_evidence_ids must contain EvidenceId objects"
            )

        if len(set(normalized_related)) != len(normalized_related):
            raise EvidenceValidationError(
                "related_evidence_ids must not contain duplicates"
            )

        if self.evidence_id in normalized_related:
            raise EvidenceValidationError(
                "a status event cannot relate Evidence to itself"
            )

        object.__setattr__(
            self,
            "related_evidence_ids",
            normalized_related,
        )

    def _identity_payload(self) -> dict[str, Any]:
        """Return the canonical status-event identity payload."""

        return {
            "evidence_id": self.evidence_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "sequence": self.sequence,
            "reason": self.reason,
            "related_evidence_ids": self.related_evidence_ids,
        }

    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceId,
        previous_status: EvidenceStatus,
        new_status: EvidenceStatus,
        sequence: int,
        reason: str,
        related_evidence_ids: Iterable[EvidenceId] = (),
    ) -> "EvidenceStatusEvent":
        """Create a validated, normalized, deterministically identified event."""

        provisional = cls(
            event_id=_placeholder_status_event_id(),
            evidence_id=evidence_id,
            previous_status=previous_status,
            new_status=new_status,
            sequence=sequence,
            reason=reason,
            related_evidence_ids=tuple(related_evidence_ids),
        )

        canonical_id = EvidenceStatusEventId.from_payload(
            provisional._identity_payload()
        )

        return replace(
            provisional,
            event_id=canonical_id,
        )

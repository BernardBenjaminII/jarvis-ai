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

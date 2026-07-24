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

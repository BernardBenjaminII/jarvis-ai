"""Validation for Genesis IV-A3 claim objects."""

from __future__ import annotations

from .claim import (
    ClaimRecord,
    ClaimStatus,
    make_claim_id,
)
from .errors import CognitionValidationError
from .evidence_validation import validate_evidence_chain


def validate_claim_record(claim: ClaimRecord) -> None:
    """Validate one immutable claim and its evidence chain."""

    if not isinstance(claim, ClaimRecord):
        raise CognitionValidationError(
            "Expected a ClaimRecord."
        )

    validate_evidence_chain(claim.evidence_chain)

    expected_id = make_claim_id(claim.identity_payload())

    if claim.claim_id != expected_id:
        raise CognitionValidationError(
            "Claim identity verification failed."
        )

    evidence_observation_ids = {
        observation_id
        for evidence in claim.evidence_chain.evidence
        for observation_id in evidence.observation_ids
    }

    missing_observation_ids = (
        set(claim.observation_ids)
        - evidence_observation_ids
    )

    if missing_observation_ids:
        raise CognitionValidationError(
            "Claim references observations absent from its evidence chain: "
            f"{sorted(missing_observation_ids)!r}"
        )

    if claim.status is ClaimStatus.CONTESTED:
        if not claim.evidence_chain.is_contested:
            raise CognitionValidationError(
                "A contested claim requires a contested evidence chain."
            )

    if claim.status is ClaimStatus.REJECTED:
        if not claim.evidence_chain.opposing_evidence:
            raise CognitionValidationError(
                "A rejected claim requires opposing evidence."
            )

    if claim.status is ClaimStatus.SUPPORTED:
        if not claim.evidence_chain.supporting_evidence:
            raise CognitionValidationError(
                "A supported claim requires supporting evidence."
            )


def validate_claim_object(value: object) -> None:
    """Validate supported Genesis IV-A3 claim objects."""

    if isinstance(value, ClaimRecord):
        validate_claim_record(value)
        return

    raise CognitionValidationError(
        "Unsupported Genesis IV-A3 claim object."
    )

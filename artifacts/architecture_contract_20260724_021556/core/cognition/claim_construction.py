"""Deterministic claim construction for Genesis IV-A3.

The claim construction engine transforms validated observations and evidence
chains into immutable claims. It does not generate hypotheses, infer hidden
causes, resolve contradictions, or choose executive actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .claim import (
    ClaimKind,
    ClaimPolarity,
    ClaimPredicate,
    ClaimRecord,
    ClaimScope,
    ClaimStatus,
)
from .contracts import Metadata, Observation, normalize_metadata
from .errors import CognitionValidationError
from .evidence import EvidenceDirection
from .evidence_chain import EvidenceChain, EvidenceChainStatus
from .evidence_validation import validate_evidence_chain
from .normalization import normalize_display_text


@dataclass(frozen=True, slots=True)
class ClaimConstructionPolicy:
    """Deterministic policy controlling claim construction."""

    supported_threshold: Decimal = Decimal("0.60")
    rejected_threshold: Decimal = Decimal("0.60")
    minimum_evidence_count: int = 1
    contested_confidence_penalty: Decimal = Decimal("0.15")
    insufficient_confidence_ceiling: Decimal = Decimal("0.49")

    def __post_init__(self) -> None:
        for field_name in (
            "supported_threshold",
            "rejected_threshold",
            "contested_confidence_penalty",
            "insufficient_confidence_ceiling",
        ):
            value = Decimal(str(getattr(self, field_name)))

            if value < Decimal("0") or value > Decimal("1"):
                raise CognitionValidationError(
                    f"{field_name} must be between zero and one."
                )

            object.__setattr__(self, field_name, value)

        if self.minimum_evidence_count < 1:
            raise CognitionValidationError(
                "minimum_evidence_count must be at least one."
            )


@dataclass(frozen=True, slots=True)
class ClaimCandidate:
    """Pre-commit claim representation."""

    observation: Observation
    evidence_chain: EvidenceChain
    kind: ClaimKind
    polarity: ClaimPolarity = ClaimPolarity.AFFIRMATIVE
    scope: ClaimScope = ClaimScope.SPECIFIC
    description: str | None = None
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        if not isinstance(self.observation, Observation):
            raise CognitionValidationError(
                "ClaimCandidate.observation must be an Observation."
            )

        if not isinstance(self.evidence_chain, EvidenceChain):
            raise CognitionValidationError(
                "ClaimCandidate.evidence_chain must be an EvidenceChain."
            )

        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                normalize_display_text(self.description),
            )

        object.__setattr__(
            self,
            "metadata",
            normalize_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class ClaimConstructionResult:
    """Result of one deterministic claim-construction operation."""

    claim: ClaimRecord
    supporting_count: int
    opposing_count: int
    neutral_count: int
    status_reason: str


class ClaimConstructionEngine:
    """Construct immutable claims from observations and evidence chains."""

    def __init__(
        self,
        *,
        policy: ClaimConstructionPolicy | None = None,
    ) -> None:
        self._policy = policy or ClaimConstructionPolicy()

    @property
    def policy(self) -> ClaimConstructionPolicy:
        return self._policy

    def construct(
        self,
        candidate: ClaimCandidate,
    ) -> ClaimConstructionResult:
        """Construct and validate one claim."""

        if not isinstance(candidate, ClaimCandidate):
            raise CognitionValidationError(
                "construct() requires a ClaimCandidate."
            )

        validate_evidence_chain(candidate.evidence_chain)
        self._validate_chain_alignment(candidate)

        supporting = tuple(
            record
            for record in candidate.evidence_chain.evidence
            if record.direction is EvidenceDirection.SUPPORTS
        )
        opposing = tuple(
            record
            for record in candidate.evidence_chain.evidence
            if record.direction is EvidenceDirection.OPPOSES
        )
        neutral = tuple(
            record
            for record in candidate.evidence_chain.evidence
            if record.direction is EvidenceDirection.NEUTRAL
        )

        status, status_reason = self._determine_status(
            chain=candidate.evidence_chain,
            supporting_count=len(supporting),
            opposing_count=len(opposing),
        )

        confidence = self._derive_confidence(
            chain=candidate.evidence_chain,
            status=status,
        )

        predicate = ClaimPredicate(
            subject=candidate.observation.subject,
            predicate=candidate.observation.predicate,
            object_value=candidate.observation.value,
        )

        metadata_map = dict(candidate.metadata)
        metadata_map.update(
            {
                "construction_policy": "genesis_iv_a3_default",
                "evidence_chain_status": (
                    candidate.evidence_chain.status.value
                ),
                "neutral_evidence_count": str(len(neutral)),
                "opposing_evidence_count": str(len(opposing)),
                "status_reason": status_reason,
                "supporting_evidence_count": str(len(supporting)),
            }
        )

        claim = ClaimRecord(
            predicate=predicate,
            evidence_chain=candidate.evidence_chain,
            kind=candidate.kind,
            polarity=candidate.polarity,
            status=status,
            scope=candidate.scope,
            confidence=confidence,
            observation_ids=(
                candidate.observation.observation_id,
            ),
            description=candidate.description,
            metadata=normalize_metadata(metadata_map),
        )

        return ClaimConstructionResult(
            claim=claim,
            supporting_count=len(supporting),
            opposing_count=len(opposing),
            neutral_count=len(neutral),
            status_reason=status_reason,
        )

    def construct_many(
        self,
        candidates: Iterable[ClaimCandidate],
    ) -> tuple[ClaimConstructionResult, ...]:
        """Construct claims in deterministic output order."""

        results = [
            self.construct(candidate)
            for candidate in candidates
        ]

        return tuple(
            sorted(
                results,
                key=lambda result: result.claim.claim_id,
            )
        )

    def _validate_chain_alignment(
        self,
        candidate: ClaimCandidate,
    ) -> None:
        observation_id = candidate.observation.observation_id

        evidence_observation_ids = {
            observation_id_value
            for evidence in candidate.evidence_chain.evidence
            for observation_id_value in evidence.observation_ids
        }

        if observation_id not in evidence_observation_ids:
            raise CognitionValidationError(
                "The evidence chain does not reference the candidate "
                "observation."
            )

        if candidate.evidence_chain.subject_id not in {
            observation_id,
            *evidence_observation_ids,
        }:
            raise CognitionValidationError(
                "Evidence-chain subject is not aligned with the candidate "
                "observation."
            )

    def _determine_status(
        self,
        *,
        chain: EvidenceChain,
        supporting_count: int,
        opposing_count: int,
    ) -> tuple[ClaimStatus, str]:
        policy = self._policy
        total_directional = supporting_count + opposing_count

        if len(chain.evidence) < policy.minimum_evidence_count:
            return (
                ClaimStatus.INSUFFICIENT,
                "minimum_evidence_count_not_met",
            )

        if total_directional == 0:
            return (
                ClaimStatus.INSUFFICIENT,
                "no_directional_evidence",
            )

        if supporting_count and opposing_count:
            return (
                ClaimStatus.CONTESTED,
                "supporting_and_opposing_evidence_present",
            )

        if chain.status is EvidenceChainStatus.INSUFFICIENT:
            return (
                ClaimStatus.INSUFFICIENT,
                "evidence_chain_marked_insufficient",
            )

        if supporting_count:
            if chain.confidence >= policy.supported_threshold:
                return (
                    ClaimStatus.SUPPORTED,
                    "supporting_evidence_threshold_met",
                )

            return (
                ClaimStatus.PROPOSED,
                "supporting_evidence_below_threshold",
            )

        if opposing_count:
            if chain.confidence >= policy.rejected_threshold:
                return (
                    ClaimStatus.REJECTED,
                    "opposing_evidence_threshold_met",
                )

            return (
                ClaimStatus.PROPOSED,
                "opposing_evidence_below_threshold",
            )

        return (
            ClaimStatus.PROPOSED,
            "claim_remains_unresolved",
        )

    def _derive_confidence(
        self,
        *,
        chain: EvidenceChain,
        status: ClaimStatus,
    ) -> Decimal:
        policy = self._policy
        confidence = Decimal(str(chain.confidence))

        if status is ClaimStatus.CONTESTED:
            confidence -= policy.contested_confidence_penalty

        if status is ClaimStatus.INSUFFICIENT:
            confidence = min(
                confidence,
                policy.insufficient_confidence_ceiling,
            )

        return max(
            Decimal("0"),
            min(Decimal("1"), confidence),
        )


def construct_claim(
    candidate: ClaimCandidate,
    *,
    policy: ClaimConstructionPolicy | None = None,
) -> ClaimConstructionResult:
    """Convenience function for deterministic claim construction."""

    return ClaimConstructionEngine(
        policy=policy,
    ).construct(candidate)

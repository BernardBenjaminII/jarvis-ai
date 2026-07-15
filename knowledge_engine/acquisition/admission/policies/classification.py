"""
Candidate-classification admission policy.

Recognized knowledge-bearing candidate types are accepted.
Explicitly prohibited types are rejected.
Everything else requires review.
"""

from __future__ import annotations

from collections.abc import Iterable

from knowledge_engine.acquisition.admission.models import (
    AdmissionAction,
    AdmissionContext,
    PolicyEvaluation,
)
from knowledge_engine.acquisition.admission.policies.base import (
    AdmissionPolicy,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


DEFAULT_ACCEPTED_TYPES = frozenset({
    "document",
    "image",
    "source_code",
})

DEFAULT_REVIEW_TYPES = frozenset({
    "generic_file",
})

DEFAULT_REJECTED_TYPES = frozenset()


def _normalize_types(
    values: Iterable[str],
) -> frozenset[str]:
    normalized = frozenset(
        value.strip().lower()
        for value in values
        if value.strip()
    )

    return normalized


class ClassificationAdmissionPolicy(AdmissionPolicy):
    """Evaluate the provider-assigned candidate classification."""

    policy_id = "classification"
    priority = 40

    def __init__(
        self,
        *,
        accepted_types: Iterable[str] = DEFAULT_ACCEPTED_TYPES,
        review_types: Iterable[str] = DEFAULT_REVIEW_TYPES,
        rejected_types: Iterable[str] = DEFAULT_REJECTED_TYPES,
    ):
        self.accepted_types = _normalize_types(
            accepted_types
        )

        self.review_types = _normalize_types(
            review_types
        )

        self.rejected_types = _normalize_types(
            rejected_types
        )

        overlap = (
            self.accepted_types & self.review_types
            | self.accepted_types & self.rejected_types
            | self.review_types & self.rejected_types
        )

        if overlap:
            raise ValueError(
                "Candidate types cannot belong to multiple policy "
                "groups: "
                + ", ".join(sorted(overlap))
            )

    def evaluate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext,
    ) -> PolicyEvaluation:
        del context

        candidate_type = (
            candidate.candidate_type
            .strip()
            .lower()
        )

        if candidate_type in self.rejected_types:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.REJECT,
                reason_code="rejected_candidate_type",
                message=(
                    f"Candidate type {candidate_type!r} is prohibited."
                ),
                details={
                    "candidate_type": candidate_type,
                    "classification": "rejected",
                },
            )

        if candidate_type in self.accepted_types:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.ACCEPT,
                reason_code="accepted_candidate_type",
                message=(
                    f"Candidate type {candidate_type!r} is approved."
                ),
                details={
                    "candidate_type": candidate_type,
                    "classification": "accepted",
                },
            )

        return PolicyEvaluation(
            policy_id=self.policy_id,
            priority=self.priority,
            action=AdmissionAction.REVIEW,
            reason_code="unclassified_candidate_type",
            message=(
                f"Candidate type {candidate_type!r} requires review."
            ),
            details={
                "candidate_type": candidate_type,
                "classification": "review",
            },
        )


__all__ = [
    "ClassificationAdmissionPolicy",
    "DEFAULT_ACCEPTED_TYPES",
    "DEFAULT_REJECTED_TYPES",
    "DEFAULT_REVIEW_TYPES",
]

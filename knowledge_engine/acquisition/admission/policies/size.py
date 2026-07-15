"""
Candidate-size admission policy.

Normal candidates are accepted.
Large candidates require review.
Candidates beyond the configured hard limit are rejected.
"""

from __future__ import annotations

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


class SizeAdmissionPolicy(AdmissionPolicy):
    """Evaluate candidate size against deterministic thresholds."""

    policy_id = "size"
    priority = 30

    def __init__(
        self,
        *,
        review_above_bytes: int = 100 * 1024 * 1024,
        reject_above_bytes: int = 2 * 1024 * 1024 * 1024,
    ):
        if review_above_bytes < 0:
            raise ValueError(
                "review_above_bytes must not be negative"
            )

        if reject_above_bytes < 1:
            raise ValueError(
                "reject_above_bytes must be at least 1"
            )

        if review_above_bytes >= reject_above_bytes:
            raise ValueError(
                "review_above_bytes must be less than "
                "reject_above_bytes"
            )

        self.review_above_bytes = review_above_bytes
        self.reject_above_bytes = reject_above_bytes

    def evaluate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext,
    ) -> PolicyEvaluation:
        del context

        size_bytes = candidate.size_bytes

        if size_bytes > self.reject_above_bytes:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.REJECT,
                reason_code="size_exceeds_limit",
                message=(
                    "Candidate exceeds the maximum configured "
                    "admission size."
                ),
                details={
                    "size_bytes": size_bytes,
                    "review_above_bytes": (
                        self.review_above_bytes
                    ),
                    "reject_above_bytes": (
                        self.reject_above_bytes
                    ),
                },
            )

        if size_bytes > self.review_above_bytes:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.REVIEW,
                reason_code="large_candidate",
                message=(
                    "Candidate exceeds the automatic-admission size "
                    "and requires review."
                ),
                details={
                    "size_bytes": size_bytes,
                    "review_above_bytes": (
                        self.review_above_bytes
                    ),
                    "reject_above_bytes": (
                        self.reject_above_bytes
                    ),
                },
            )

        return PolicyEvaluation(
            policy_id=self.policy_id,
            priority=self.priority,
            action=AdmissionAction.ACCEPT,
            reason_code="size_within_limit",
            message=(
                "Candidate size is within automatic-admission limits."
            ),
            details={
                "size_bytes": size_bytes,
                "review_above_bytes": (
                    self.review_above_bytes
                ),
                "reject_above_bytes": (
                    self.reject_above_bytes
                ),
            },
        )


__all__ = [
    "SizeAdmissionPolicy",
]

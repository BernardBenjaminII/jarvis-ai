"""
Exact-checksum duplicate admission policy.

This policy compares a candidate's SHA-256 checksum against the immutable
known-checksum set supplied through AdmissionContext.

It performs no database queries and has no side effects.
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


class ExactDuplicatePolicy(AdmissionPolicy):
    """Ignore candidates whose exact checksum is already known."""

    policy_id = "exact_duplicate"
    priority = 10

    def evaluate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext,
    ) -> PolicyEvaluation:
        checksum = candidate.checksum_sha256.strip().lower()

        if checksum in context.known_checksums:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.IGNORE,
                reason_code="exact_duplicate",
                message=(
                    "Candidate checksum already exists in the known "
                    "checksum set."
                ),
                details={
                    "checksum_sha256": checksum,
                    "duplicate": True,
                },
            )

        return PolicyEvaluation(
            policy_id=self.policy_id,
            priority=self.priority,
            action=AdmissionAction.ACCEPT,
            reason_code="checksum_not_known",
            message=(
                "Candidate checksum is not present in the known "
                "checksum set."
            ),
            details={
                "checksum_sha256": checksum,
                "duplicate": False,
            },
        )


__all__ = [
    "ExactDuplicatePolicy",
]

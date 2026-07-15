"""
Deterministic admission-policy orchestration.

The AdmissionDirector owns:

- ordered policy execution
- policy-result validation
- single-candidate evaluation
- deterministic batch evaluation
- immutable AdmissionDecision creation

It does not:

- modify candidates
- write databases
- write acquisition queues
- invoke assimilation
- access external networks
"""

from __future__ import annotations

from collections.abc import Iterable

from knowledge_engine.acquisition.admission.models import (
    AdmissionContext,
    AdmissionDecision,
    PolicyEvaluation,
)
from knowledge_engine.acquisition.admission.registry import (
    AdmissionPolicyRegistry,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


class AdmissionDirector:
    """
    Evaluate acquisition candidates through an ordered policy registry.
    """

    def __init__(
        self,
        registry: AdmissionPolicyRegistry,
    ):
        if not isinstance(
            registry,
            AdmissionPolicyRegistry,
        ):
            raise TypeError(
                "registry must be an AdmissionPolicyRegistry"
            )

        self.registry = registry

    def evaluate_candidate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext | None = None,
    ) -> AdmissionDecision:
        """
        Evaluate one candidate through every registered policy.

        Policies always execute in registry order.

        Raises:
            RuntimeError:
                If no policies are registered or a policy returns an
                inconsistent result.
        """

        resolved_context = (
            context
            if context is not None
            else AdmissionContext()
        )

        policies = self.registry.ordered_policies()

        if not policies:
            raise RuntimeError(
                "No admission policies are registered"
            )

        evaluations = tuple(
            policy.evaluate(
                candidate=candidate,
                context=resolved_context,
            )
            for policy in policies
        )

        self._validate_evaluations(
            evaluations=evaluations,
        )

        return AdmissionDecision(
            candidate=candidate,
            evaluations=evaluations,
        )

    def evaluate_candidates(
        self,
        *,
        candidates: Iterable[SourceCandidate],
        context: AdmissionContext | None = None,
    ) -> tuple[AdmissionDecision, ...]:
        """
        Evaluate a candidate collection in deterministic local-path order.

        Candidate paths must be unique.
        """

        ordered_candidates = tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    candidate.local_path,
                    candidate.provider_id,
                    candidate.source_uri,
                ),
            )
        )

        local_paths = tuple(
            candidate.local_path
            for candidate in ordered_candidates
        )

        if len(local_paths) != len(
            set(local_paths)
        ):
            raise ValueError(
                "Candidate local paths must be unique"
            )

        return tuple(
            self.evaluate_candidate(
                candidate=candidate,
                context=context,
            )
            for candidate in ordered_candidates
        )

    def _validate_evaluations(
        self,
        *,
        evaluations: tuple[
            PolicyEvaluation,
            ...,
        ],
    ) -> None:
        """
        Verify that policy results match the canonical registry order.
        """

        expected_ids = self.registry.policy_ids()

        returned_ids = tuple(
            evaluation.policy_id
            for evaluation in evaluations
        )

        if returned_ids != expected_ids:
            raise RuntimeError(
                "Policy evaluations do not match registry order"
            )

        returned_priorities = tuple(
            evaluation.priority
            for evaluation in evaluations
        )

        expected_priorities = tuple(
            policy.priority
            for policy in self.registry.ordered_policies()
        )

        if returned_priorities != expected_priorities:
            raise RuntimeError(
                "Policy evaluations contain mismatched priorities"
            )

        if len(returned_ids) != len(
            set(returned_ids)
        ):
            raise RuntimeError(
                "Policy evaluations contain duplicate policy IDs"
            )


__all__ = [
    "AdmissionDirector",
]

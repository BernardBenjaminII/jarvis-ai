"""
Ordered registry for JARVIS acquisition-admission policies.

The registry owns:

- unique policy registration
- policy lookup
- deterministic execution ordering
- public policy inventory

It does not:

- execute policies
- evaluate candidates
- persist policy state
- mutate source candidates
"""

from __future__ import annotations

from knowledge_engine.acquisition.admission.policies.base import (
    AdmissionPolicy,
)


class AdmissionPolicyRegistry:
    """
    Register and resolve acquisition-admission policies.

    Policies are ordered by:

    1. ascending priority
    2. ascending policy_id

    This ordering is deterministic across processes and platforms.
    """

    def __init__(self) -> None:
        self._policies: dict[
            str,
            AdmissionPolicy,
        ] = {}

    def register(
        self,
        policy: AdmissionPolicy,
    ) -> None:
        """
        Register exactly one policy for one policy_id.

        Raises:
            ValueError:
                If policy_id is blank, priority is invalid, or a policy
                with the same ID is already registered.
        """

        policy_id = policy.policy_id.strip()

        if not policy_id:
            raise ValueError(
                "policy_id must not be empty"
            )

        if policy.priority < 0:
            raise ValueError(
                "policy priority must not be negative"
            )

        if policy_id in self._policies:
            raise ValueError(
                f"Policy already registered: {policy_id}"
            )

        self._policies[policy_id] = policy

    def get(
        self,
        policy_id: str,
    ) -> AdmissionPolicy:
        """
        Return one registered policy by stable ID.

        Raises:
            ValueError:
                If policy_id is blank.

            LookupError:
                If the policy is not registered.
        """

        normalized = policy_id.strip()

        if not normalized:
            raise ValueError(
                "policy_id must not be empty"
            )

        try:
            return self._policies[normalized]
        except KeyError as exc:
            raise LookupError(
                f"No admission policy registered: {normalized}"
            ) from exc

    def supports(
        self,
        policy_id: str,
    ) -> bool:
        """Return whether a policy ID is registered."""

        normalized = policy_id.strip()

        if not normalized:
            return False

        return normalized in self._policies

    def ordered_policies(
        self,
    ) -> tuple[AdmissionPolicy, ...]:
        """
        Return all policies in deterministic execution order.
        """

        return tuple(
            sorted(
                self._policies.values(),
                key=lambda policy: (
                    policy.priority,
                    policy.policy_id,
                ),
            )
        )

    def policy_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return policy IDs in deterministic execution order.
        """

        return tuple(
            policy.policy_id
            for policy in self.ordered_policies()
        )

    def __len__(self) -> int:
        """Return the number of registered policies."""

        return len(self._policies)


__all__ = [
    "AdmissionPolicyRegistry",
]

"""
Canonical admission models.

This module defines the immutable contracts used by the acquisition
admission subsystem.

Responsibilities
----------------
* immutable decision objects
* deterministic serialization
* validation
* stable SHA-256 fingerprints

This module intentionally contains:

    • no filesystem logic
    • no database logic
    • no provider logic
    • no policy execution

Everything here must be deterministic.
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field

from enum import Enum

from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence

from knowledge_engine.acquisition.models import SourceCandidate


###############################################################################
# Helpers
###############################################################################


def _stable_json(data: Any) -> str:
    """
    Deterministic JSON encoding.
    """

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _fingerprint(data: Any) -> str:
    """
    Stable SHA-256 fingerprint.
    """

    return hashlib.sha256(
        _stable_json(data).encode("utf-8")
    ).hexdigest()


###############################################################################
# Admission Action
###############################################################################


class AdmissionAction(str, Enum):
    """
    Canonical admission outcomes.
    """

    ACCEPT = "accept"

    REVIEW = "review"

    IGNORE = "ignore"

    REJECT = "reject"


###############################################################################
# Admission Context
###############################################################################


@dataclass(frozen=True, slots=True)
class AdmissionContext:
    """
    Immutable evaluation context supplied to every policy.
    """

    known_checksums: frozenset[str] = field(default_factory=frozenset)

    campaign_id: str | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):

        object.__setattr__(
            self,
            "known_checksums",
            frozenset(self.known_checksums),
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "known_checksums": sorted(self.known_checksums),
            "campaign_id": self.campaign_id,
            "metadata": dict(self.metadata),
        }

    @property
    def fingerprint(self) -> str:

        return _fingerprint(self.to_dict())


###############################################################################
# Policy Evaluation
###############################################################################


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """
    Result returned by a single admission policy.
    """

    policy_id: str

    priority: int

    action: AdmissionAction

    reason_code: str

    message: str

    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):

        if not self.policy_id.strip():
            raise ValueError(
                "policy_id cannot be empty."
            )

        if self.priority < 0:
            raise ValueError(
                "priority must be >= 0."
            )

        if not self.reason_code.strip():
            raise ValueError(
                "reason_code cannot be empty."
            )

        if not self.message.strip():
            raise ValueError(
                "message cannot be empty."
            )

    def to_dict(self) -> dict[str, Any]:

        return {
            "policy_id": self.policy_id,
            "priority": self.priority,
            "action": self.action.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "details": dict(self.details),
        }

    @property
    def fingerprint(self) -> str:

        return _fingerprint(
            self.to_dict()
        )
###############################################################################
# Admission Decision
###############################################################################


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """
    Final admission decision produced after all policies have executed.

    Policy precedence (highest to lowest):

        REJECT
        REVIEW
        IGNORE
        ACCEPT

    The decision is completely deterministic.
    """

    candidate: SourceCandidate

    evaluations: Sequence[PolicyEvaluation]

    def __post_init__(self):

        if not self.evaluations:
            raise ValueError(
                "At least one PolicyEvaluation is required."
            )

        ordered = tuple(
            sorted(
                self.evaluations,
                key=lambda e: (
                    e.priority,
                    e.policy_id,
                ),
            )
        )

        object.__setattr__(
            self,
            "evaluations",
            ordered,
        )

    ###########################################################################
    # Final Action
    ###########################################################################

    @property
    def action(self) -> AdmissionAction:

        actions = {
            evaluation.action
            for evaluation in self.evaluations
        }

        if AdmissionAction.REJECT in actions:
            return AdmissionAction.REJECT

        if AdmissionAction.REVIEW in actions:
            return AdmissionAction.REVIEW

        if AdmissionAction.IGNORE in actions:
            return AdmissionAction.IGNORE

        return AdmissionAction.ACCEPT

    ###########################################################################
    # Convenience Properties
    ###########################################################################

    @property
    def accepted(self) -> bool:

        return self.action is AdmissionAction.ACCEPT

    @property
    def requires_review(self) -> bool:

        return self.action is AdmissionAction.REVIEW

    @property
    def ignored(self) -> bool:

        return self.action is AdmissionAction.IGNORE

    @property
    def rejected(self) -> bool:

        return self.action is AdmissionAction.REJECT

    @property
    def terminal(self) -> bool:
        """
        REVIEW is intentionally non-terminal.

        REJECT and IGNORE terminate the acquisition path.
        ACCEPT continues into mission planning.
        """

        return self.action in {
            AdmissionAction.REJECT,
            AdmissionAction.IGNORE,
        }

    ###########################################################################
    # Serialization
    ###########################################################################

    def to_dict(self) -> dict[str, Any]:

        if hasattr(self.candidate, "to_dict"):
            candidate = self.candidate.to_dict()
        elif hasattr(self.candidate, "__dict__"):
            candidate = dict(self.candidate.__dict__)
        else:
            try:
                candidate = asdict(self.candidate)
            except Exception:
                candidate = {
                    "repr": repr(self.candidate),
                }

        return {
            "candidate": candidate,
            "action": self.action.value,
            "evaluations": [
                evaluation.to_dict()
                for evaluation in self.evaluations
            ],
        }

    ###########################################################################
    # Fingerprint
    ###########################################################################

    @property
    def fingerprint(self) -> str:

        return _fingerprint(
            self.to_dict()
        )

    ###########################################################################
    # Representation
    ###########################################################################

    def __str__(self) -> str:

        return (
            f"AdmissionDecision("
            f"action={self.action.value}, "
            f"evaluations={len(self.evaluations)})"
        )


###############################################################################
# Public Exports
###############################################################################

__all__ = [
    "AdmissionAction",
    "AdmissionContext",
    "PolicyEvaluation",
    "AdmissionDecision",
]

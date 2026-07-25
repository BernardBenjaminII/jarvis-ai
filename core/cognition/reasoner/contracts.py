"""Protocols for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.cognition.evidence_correlation import HypothesisAssessment
from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .models import (
    ExecutiveReasoningResult,
    ReasoningPolicy,
    ReasoningQuery,
)


@runtime_checkable
class ExecutiveReasoner(Protocol):
    """Produces a justified judgment over competing hypotheses."""

    def reason(
        self,
        *,
        situation: SituationSnapshot,
        hypotheses: Sequence[Hypothesis],
        assessments: Sequence[HypothesisAssessment],
        policy: ReasoningPolicy | None = None,
    ) -> ExecutiveReasoningResult:
        """Return a deterministic executive reasoning result."""


@runtime_checkable
class ReasoningRepository(Protocol):
    """Persistence boundary for executive reasoning results."""

    def put(self, result: ExecutiveReasoningResult) -> bool:
        """Insert a result and return False for a duplicate ID."""

    def get(self, reasoning_id: str) -> ExecutiveReasoningResult:
        """Return one result."""

    def query(
        self,
        query: ReasoningQuery,
    ) -> Sequence[ExecutiveReasoningResult]:
        """Return matching results."""

    def count(self) -> int:
        """Return repository size."""

    def close(self) -> None:
        """Close the repository."""

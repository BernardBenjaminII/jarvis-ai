"""Public protocols for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.cognition.situation import SituationSnapshot

from .models import Hypothesis, HypothesisProposal, HypothesisQuery


@runtime_checkable
class HypothesisRepository(Protocol):
    """Persistence boundary for executive hypotheses."""

    def put(self, hypothesis: Hypothesis) -> bool:
        """Insert a hypothesis and return False for a duplicate ID."""

    def get(self, hypothesis_id: str) -> Hypothesis:
        """Return one hypothesis."""

    def query(self, query: HypothesisQuery) -> Sequence[Hypothesis]:
        """Return matching hypotheses."""

    def count(self) -> int:
        """Return repository size."""

    def close(self) -> None:
        """Close the repository."""


@runtime_checkable
class HypothesisGenerator(Protocol):
    """Generates candidate hypotheses from an executive situation."""

    def generate(
        self,
        *,
        situation: SituationSnapshot,
        proposals: Sequence[HypothesisProposal],
    ) -> Sequence[Hypothesis]:
        """Generate deterministic candidate hypotheses."""

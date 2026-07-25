"""Public protocols for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.cognition.observation import Observation

from .models import SituationQuery, SituationRelation, SituationSnapshot


@runtime_checkable
class SituationRepository(Protocol):
    """Persistence boundary for executive situations."""

    def put(self, situation: SituationSnapshot) -> bool:
        """Insert a new situation and return False for a duplicate ID."""

    def get(self, situation_id: str) -> SituationSnapshot:
        """Return one situation."""

    def query(self, query: SituationQuery) -> Sequence[SituationSnapshot]:
        """Return matching situations."""

    def count(self) -> int:
        """Return repository size."""

    def close(self) -> None:
        """Close the repository."""


@runtime_checkable
class SituationProjector(Protocol):
    """Transforms observations into an executive situation."""

    def project(
        self,
        *,
        title: str,
        observations: Sequence[Observation],
        relations: Sequence[SituationRelation] = (),
        summary: str | None = None,
    ) -> SituationSnapshot:
        """Project observations into a canonical situation."""

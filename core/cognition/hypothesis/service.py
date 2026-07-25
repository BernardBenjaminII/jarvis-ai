"""Application service for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations

from typing import Sequence

from core.cognition.situation import SituationSnapshot

from .enums import HypothesisDisposition
from .generator import ExecutiveHypothesisGenerator
from .models import Hypothesis, HypothesisProposal
from .repository import InMemoryHypothesisRepository


class ExecutiveHypothesisService:
    """Generate and persist candidate hypotheses."""

    def __init__(
        self,
        repository: InMemoryHypothesisRepository,
        generator: ExecutiveHypothesisGenerator | None = None,
    ) -> None:
        if not isinstance(repository, InMemoryHypothesisRepository):
            raise TypeError(
                "repository must be InMemoryHypothesisRepository"
            )
        self._repository = repository
        self._generator = generator or ExecutiveHypothesisGenerator()

    @property
    def repository(self) -> InMemoryHypothesisRepository:
        """Return the configured repository."""

        return self._repository

    def propose(
        self,
        *,
        situation: SituationSnapshot,
        proposals: Sequence[HypothesisProposal],
    ) -> tuple[
        tuple[Hypothesis, HypothesisDisposition],
        ...,
    ]:
        """Generate and persist candidate hypotheses."""

        hypotheses = self._generator.generate(
            situation=situation,
            proposals=proposals,
        )

        results: list[tuple[Hypothesis, HypothesisDisposition]] = []
        for hypothesis in hypotheses:
            inserted = self._repository.put(hypothesis)
            disposition = (
                HypothesisDisposition.CREATED
                if inserted
                else HypothesisDisposition.DUPLICATE
            )
            results.append((hypothesis, disposition))

        return tuple(results)

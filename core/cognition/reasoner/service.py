"""Application service for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations

from typing import Sequence

from core.cognition.evidence_correlation import HypothesisAssessment
from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .engine import DeterministicExecutiveReasoner
from .enums import ReasoningRepositoryDisposition
from .models import ExecutiveReasoningResult, ReasoningPolicy
from .repository import InMemoryReasoningRepository


class ExecutiveReasoningService:
    """Reason over assessed hypotheses and persist the result."""

    def __init__(
        self,
        repository: InMemoryReasoningRepository,
        reasoner: DeterministicExecutiveReasoner | None = None,
    ) -> None:
        if not isinstance(repository, InMemoryReasoningRepository):
            raise TypeError(
                "repository must be InMemoryReasoningRepository"
            )
        self._repository = repository
        self._reasoner = reasoner or DeterministicExecutiveReasoner()

    @property
    def repository(self) -> InMemoryReasoningRepository:
        return self._repository

    def reason(
        self,
        *,
        situation: SituationSnapshot,
        hypotheses: Sequence[Hypothesis],
        assessments: Sequence[HypothesisAssessment],
        policy: ReasoningPolicy | None = None,
    ) -> tuple[
        ExecutiveReasoningResult,
        ReasoningRepositoryDisposition,
    ]:
        result = self._reasoner.reason(
            situation=situation,
            hypotheses=hypotheses,
            assessments=assessments,
            policy=policy,
        )
        inserted = self._repository.put(result)
        disposition = (
            ReasoningRepositoryDisposition.CREATED
            if inserted
            else ReasoningRepositoryDisposition.DUPLICATE
        )
        return result, disposition

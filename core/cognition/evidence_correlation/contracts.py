"""Protocols for Genesis IV-A4 Executive Evidence Correlation Engine."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .models import AssessmentQuery, EvidenceLink, HypothesisAssessment


@runtime_checkable
class AssessmentRepository(Protocol):
    """Persistence boundary for hypothesis assessments."""

    def put(self, assessment: HypothesisAssessment) -> bool:
        """Insert an assessment and return False for a duplicate ID."""

    def get(self, assessment_id: str) -> HypothesisAssessment:
        """Return one assessment."""

    def query(
        self,
        query: AssessmentQuery,
    ) -> Sequence[HypothesisAssessment]:
        """Return matching assessments."""

    def count(self) -> int:
        """Return repository size."""

    def close(self) -> None:
        """Close the repository."""


@runtime_checkable
class EvidenceCorrelator(Protocol):
    """Correlates evidence links against one hypothesis."""

    def assess(
        self,
        *,
        situation: SituationSnapshot,
        hypothesis: Hypothesis,
        links: Sequence[EvidenceLink],
        missing_evidence_questions: Sequence[str] = (),
    ) -> HypothesisAssessment:
        """Produce a deterministic evidence assessment."""

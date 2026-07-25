"""Application service for Genesis IV-A4 evidence correlation."""

from __future__ import annotations

from typing import Mapping, Sequence

from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .correlator import ExecutiveEvidenceCorrelator
from .enums import AssessmentDisposition
from .models import EvidenceLink, HypothesisAssessment
from .repository import InMemoryAssessmentRepository


class ExecutiveEvidenceService:
    """Correlate and persist hypothesis evidence assessments."""

    def __init__(
        self,
        repository: InMemoryAssessmentRepository,
        correlator: ExecutiveEvidenceCorrelator | None = None,
    ) -> None:
        if not isinstance(repository, InMemoryAssessmentRepository):
            raise TypeError(
                "repository must be InMemoryAssessmentRepository"
            )
        self._repository = repository
        self._correlator = correlator or ExecutiveEvidenceCorrelator()

    @property
    def repository(self) -> InMemoryAssessmentRepository:
        """Return the configured repository."""

        return self._repository

    def assess(
        self,
        *,
        situation: SituationSnapshot,
        hypothesis: Hypothesis,
        links: Sequence[EvidenceLink],
        missing_evidence_questions: Sequence[str] = (),
        rationale: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> tuple[HypothesisAssessment, AssessmentDisposition]:
        """Correlate evidence and persist one assessment."""

        assessment = self._correlator.assess(
            situation=situation,
            hypothesis=hypothesis,
            links=links,
            missing_evidence_questions=missing_evidence_questions,
            rationale=rationale,
            labels=labels,
        )
        inserted = self._repository.put(assessment)
        disposition = (
            AssessmentDisposition.CREATED
            if inserted
            else AssessmentDisposition.DUPLICATE
        )
        return assessment, disposition

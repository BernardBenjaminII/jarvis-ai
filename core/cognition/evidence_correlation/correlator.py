"""Deterministic evidence correlation for Genesis IV-A4."""

from __future__ import annotations

from typing import Mapping, Sequence

from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .enums import AssessmentStatus, EvidencePolarity
from .errors import InvalidAssessmentError
from .models import (
    EvidenceLink,
    HypothesisAssessment,
    derive_assessment_identity,
)


class ExecutiveEvidenceCorrelator:
    """Evaluate explicit evidence links without inventing new evidence."""

    def assess(
        self,
        *,
        situation: SituationSnapshot,
        hypothesis: Hypothesis,
        links: Sequence[EvidenceLink],
        missing_evidence_questions: Sequence[str] = (),
        rationale: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> HypothesisAssessment:
        """Create one deterministic hypothesis assessment."""

        if not isinstance(situation, SituationSnapshot):
            raise TypeError("situation must be SituationSnapshot")
        if not isinstance(hypothesis, Hypothesis):
            raise TypeError("hypothesis must be Hypothesis")
        if hypothesis.situation_id != situation.situation_id:
            raise InvalidAssessmentError(
                "hypothesis does not belong to the supplied situation"
            )

        normalized = tuple(links)
        if not normalized:
            raise InvalidAssessmentError(
                "at least one evidence link is required"
            )

        valid_observation_ids = set(situation.observation_ids)
        for link in normalized:
            if not isinstance(link, EvidenceLink):
                raise TypeError("links must contain EvidenceLink objects")
            if link.hypothesis_id != hypothesis.hypothesis_id:
                raise InvalidAssessmentError(
                    "evidence link targets a different hypothesis"
                )
            if link.observation_id not in valid_observation_ids:
                raise InvalidAssessmentError(
                    "evidence link references an observation outside "
                    "the source situation"
                )

        admissible = tuple(link for link in normalized if link.admissible)
        support_raw = sum(
            max(link.weighted_score, 0.0)
            for link in admissible
            if link.polarity is EvidencePolarity.SUPPORTS
        )
        contradiction_raw = sum(
            abs(min(link.weighted_score, 0.0))
            for link in admissible
            if link.polarity is EvidencePolarity.CONTRADICTS
        )

        support_score = min(support_raw, 1.0)
        contradiction_score = min(contradiction_raw, 1.0)
        net_score = max(
            -1.0,
            min(1.0, support_score - contradiction_score),
        )

        covered_ids = {
            link.observation_id
            for link in admissible
            if link.polarity is not EvidencePolarity.NEUTRAL
        }
        coverage = len(covered_ids) / len(valid_observation_ids)

        reliability = (
            sum(link.reliability for link in admissible) / len(admissible)
            if admissible
            else 0.0
        )
        confidence = max(
            0.0,
            min(
                1.0,
                hypothesis.confidence
                * (0.50 + 0.50 * coverage)
                * reliability,
            ),
        )

        questions = tuple(missing_evidence_questions)
        status = (
            AssessmentStatus.COMPLETE
            if coverage == 1.0 and not questions
            else AssessmentStatus.INCONCLUSIVE
            if net_score == 0.0
            else AssessmentStatus.PROVISIONAL
        )
        if support_score > 0.0 and contradiction_score > 0.0:
            status = AssessmentStatus.CONTESTED

        assessment_id = derive_assessment_identity(
            situation=situation,
            hypothesis=hypothesis,
            links=normalized,
        )

        return HypothesisAssessment(
            assessment_id=assessment_id,
            situation_id=situation.situation_id,
            hypothesis_id=hypothesis.hypothesis_id,
            status=status,
            links=normalized,
            support_score=support_score,
            contradiction_score=contradiction_score,
            net_score=net_score,
            coverage=coverage,
            confidence=confidence,
            missing_evidence_questions=questions,
            rationale=rationale,
            labels=tuple(sorted((labels or {}).items())),
        )

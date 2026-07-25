"""Deterministic executive reasoning for Genesis IV-A5."""

from __future__ import annotations

from typing import Sequence

from core.cognition.evidence_correlation import HypothesisAssessment
from core.cognition.hypothesis import Hypothesis
from core.cognition.situation import SituationSnapshot

from .enums import ReasoningDisposition, ReasoningStatus
from .errors import InvalidReasoningInputError
from .models import (
    ExecutiveReasoningResult,
    HypothesisRanking,
    ReasoningPolicy,
    derive_reasoning_identity,
)


class DeterministicExecutiveReasoner:
    """Rank assessed hypotheses and abstain when justification is weak."""

    def reason(
        self,
        *,
        situation: SituationSnapshot,
        hypotheses: Sequence[Hypothesis],
        assessments: Sequence[HypothesisAssessment],
        policy: ReasoningPolicy | None = None,
    ) -> ExecutiveReasoningResult:
        if not isinstance(situation, SituationSnapshot):
            raise TypeError("situation must be SituationSnapshot")

        normalized_hypotheses = tuple(hypotheses)
        normalized_assessments = tuple(assessments)
        active_policy = policy or ReasoningPolicy()

        if not normalized_hypotheses:
            raise InvalidReasoningInputError(
                "at least one hypothesis is required"
            )
        if not normalized_assessments:
            raise InvalidReasoningInputError(
                "at least one assessment is required"
            )

        by_hypothesis: dict[str, Hypothesis] = {}
        for hypothesis in normalized_hypotheses:
            if not isinstance(hypothesis, Hypothesis):
                raise TypeError("hypotheses must contain Hypothesis objects")
            if hypothesis.situation_id != situation.situation_id:
                raise InvalidReasoningInputError(
                    "hypothesis belongs to a different situation"
                )
            if hypothesis.hypothesis_id in by_hypothesis:
                raise InvalidReasoningInputError(
                    "duplicate hypothesis identity supplied"
                )
            by_hypothesis[hypothesis.hypothesis_id] = hypothesis

        assessment_by_hypothesis: dict[str, HypothesisAssessment] = {}
        for assessment in normalized_assessments:
            if not isinstance(assessment, HypothesisAssessment):
                raise TypeError(
                    "assessments must contain HypothesisAssessment objects"
                )
            if assessment.situation_id != situation.situation_id:
                raise InvalidReasoningInputError(
                    "assessment belongs to a different situation"
                )
            if assessment.hypothesis_id not in by_hypothesis:
                raise InvalidReasoningInputError(
                    "assessment references an unsupplied hypothesis"
                )
            if assessment.hypothesis_id in assessment_by_hypothesis:
                raise InvalidReasoningInputError(
                    "multiple assessments supplied for one hypothesis"
                )
            assessment_by_hypothesis[
                assessment.hypothesis_id
            ] = assessment

        missing = set(by_hypothesis) - set(assessment_by_hypothesis)
        if missing:
            raise InvalidReasoningInputError(
                f"hypotheses missing assessments: {sorted(missing)}"
            )

        scored: list[
            tuple[float, float, str, Hypothesis, HypothesisAssessment]
        ] = []
        for hypothesis_id, hypothesis in by_hypothesis.items():
            assessment = assessment_by_hypothesis[hypothesis_id]
            score = max(
                -1.0,
                min(
                    1.0,
                    assessment.net_score
                    * assessment.coverage
                    * assessment.confidence,
                ),
            )
            scored.append(
                (
                    score,
                    assessment.confidence,
                    hypothesis_id,
                    hypothesis,
                    assessment,
                )
            )

        scored.sort(
            key=lambda item: (item[0], item[1], item[2]),
            reverse=True,
        )

        rankings: list[HypothesisRanking] = []
        for index, (score, _, _, hypothesis, assessment) in enumerate(
            scored,
            start=1,
        ):
            rankings.append(
                HypothesisRanking(
                    hypothesis_id=hypothesis.hypothesis_id,
                    assessment_id=assessment.assessment_id,
                    rank=index,
                    score=score,
                    confidence=assessment.confidence,
                    support_score=assessment.support_score,
                    contradiction_score=assessment.contradiction_score,
                    coverage=assessment.coverage,
                )
            )

        top = rankings[0]
        runner_up_score = rankings[1].score if len(rankings) > 1 else 0.0
        margin = max(0.0, min(1.0, top.score - runner_up_score))

        selected_hypothesis_id: str | None = None

        if top.coverage < active_policy.minimum_coverage:
            disposition = ReasoningDisposition.DEFERRED
            rationale = (
                "Judgment deferred because the leading hypothesis lacks "
                "sufficient evidence coverage."
            )
        elif top.confidence < active_policy.minimum_confidence:
            disposition = ReasoningDisposition.DEFERRED
            rationale = (
                "Judgment deferred because the leading assessment confidence "
                "is below policy."
            )
        elif top.score < active_policy.minimum_selection_score:
            disposition = ReasoningDisposition.INCONCLUSIVE
            rationale = (
                "No hypothesis achieved the minimum justified selection score."
            )
        elif (
            top.contradiction_score
            >= active_policy.contested_contradiction_threshold
        ):
            disposition = ReasoningDisposition.CONTESTED
            rationale = (
                "The leading hypothesis remains materially contradicted."
            )
        elif len(rankings) > 1 and margin < active_policy.minimum_margin:
            disposition = ReasoningDisposition.CONTESTED
            rationale = (
                "The leading hypotheses are too closely matched for selection."
            )
        else:
            disposition = ReasoningDisposition.SELECTED
            selected_hypothesis_id = top.hypothesis_id
            rationale = (
                "The selected hypothesis has the strongest policy-compliant "
                "combination of net evidence, coverage, and confidence."
            )

        unresolved_assumptions = tuple(
            assumption
            for hypothesis in normalized_hypotheses
            for assumption in hypothesis.assumptions
        )
        evidence_requests = tuple(
            question
            for assessment in normalized_assessments
            for question in assessment.missing_evidence_questions
        )

        reasoning_id = derive_reasoning_identity(
            situation=situation,
            hypotheses=normalized_hypotheses,
            assessments=normalized_assessments,
            policy=active_policy,
        )

        confidence = max(
            0.0,
            min(1.0, top.confidence * top.coverage),
        )

        return ExecutiveReasoningResult(
            reasoning_id=reasoning_id,
            situation_id=situation.situation_id,
            status=ReasoningStatus.COMPLETE,
            disposition=disposition,
            rankings=tuple(rankings),
            selected_hypothesis_id=selected_hypothesis_id,
            confidence=confidence,
            margin=margin,
            rationale=rationale,
            unresolved_assumptions=unresolved_assumptions,
            evidence_requests=evidence_requests,
        )

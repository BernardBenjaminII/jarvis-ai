"""Deterministic Reasoning Engine service for JARVIS Phase X."""

from __future__ import annotations

from collections import Counter

from core.reasoning.enums import (
    EvidenceStance,
    HypothesisDisposition,
    ReasoningStatus,
)
from core.reasoning.errors import (
    DuplicateReasoningElementError,
    InvalidReasoningRequestError,
    UnknownEvidenceReferenceError,
)
from core.reasoning.inference import assess_hypothesis
from core.reasoning.models import (
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
)


ENGINE_VERSION = "10.0.0-foundation"


class ReasoningEngine:
    """Produce auditable conclusions from explicit evidence and hypotheses.

    Phase X is deliberately deterministic. It does not call an LLM, retrieve
    knowledge, execute tools, create runtime missions, or mutate planning data.
    """

    engine_version = ENGINE_VERSION

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Evaluate all hypotheses and produce a planning recommendation."""

        self._validate_request(request)

        evidence_by_id = {
            item.evidence_id: item
            for item in request.evidence
        }
        hypothesis_by_id = {
            item.hypothesis_id: item
            for item in request.hypotheses
        }

        assessments = tuple(
            assess_hypothesis(hypothesis, evidence_by_id)
            for hypothesis in sorted(
                request.hypotheses,
                key=lambda item: item.hypothesis_id,
            )
        )

        ranked = tuple(
            sorted(
                assessments,
                key=lambda item: (
                    -item.confidence,
                    -item.support_score,
                    item.contradiction_score,
                    item.hypothesis_id,
                ),
            )
        )

        selected = self._select_assessment(ranked)
        contradictions = self._collect_contradictions(request)
        missing_information = self._collect_missing_information(
            request=request,
            assessments=ranked,
        )
        recommendation = self._build_planning_recommendation(
            request=request,
            selected=selected,
            hypothesis_by_id=hypothesis_by_id,
            contradictions=contradictions,
        )
        status = (
            ReasoningStatus.COMPLETED
            if selected is not None
            else ReasoningStatus.INCONCLUSIVE
        )
        trace = self._build_trace(
            request=request,
            assessments=ranked,
            selected=selected,
        )

        payload = {
            "engine_version": self.engine_version,
            "session_id": f"reasoning_{request.request_id}",
            "request_id": request.request_id,
            "request_fingerprint": request.fingerprint,
            "status": status.value,
            "assessments": [item.to_dict() for item in ranked],
            "selected_hypothesis_id": (
                selected.hypothesis_id
                if selected is not None
                else None
            ),
            "missing_information": list(missing_information),
            "contradictions": list(contradictions),
            "planning_recommendation": (
                recommendation.to_dict()
                if recommendation is not None
                else None
            ),
            "trace": [item.to_dict() for item in trace],
        }

        return ReasoningResult(
            session_id=f"reasoning_{request.request_id}",
            request_id=request.request_id,
            request_fingerprint=request.fingerprint,
            status=status,
            assessments=ranked,
            selected_hypothesis_id=(
                selected.hypothesis_id
                if selected is not None
                else None
            ),
            missing_information=missing_information,
            contradictions=contradictions,
            planning_recommendation=recommendation,
            trace=trace,
            fingerprint=canonical_fingerprint(payload),
        )

    def _validate_request(self, request: ReasoningRequest) -> None:
        evidence_ids = [item.evidence_id for item in request.evidence]
        hypothesis_ids = [
            item.hypothesis_id
            for item in request.hypotheses
        ]

        duplicate_evidence = sorted(
            identifier
            for identifier, count in Counter(evidence_ids).items()
            if count > 1
        )
        duplicate_hypotheses = sorted(
            identifier
            for identifier, count in Counter(hypothesis_ids).items()
            if count > 1
        )

        duplicates = duplicate_evidence + duplicate_hypotheses
        if duplicates:
            raise DuplicateReasoningElementError(
                "Duplicate reasoning identifiers: "
                + ", ".join(duplicates)
            )

        known_evidence = set(evidence_ids)
        for hypothesis in request.hypotheses:
            referenced = set(
                hypothesis.supporting_evidence_ids
                + hypothesis.contradicting_evidence_ids
            )
            unknown = sorted(referenced - known_evidence)
            if unknown:
                raise UnknownEvidenceReferenceError(
                    f"Hypothesis {hypothesis.hypothesis_id} references "
                    f"unknown evidence: {', '.join(unknown)}"
                )

        if not request.goal.strip():
            raise InvalidReasoningRequestError(
                "Reasoning goal cannot be empty"
            )

    def _select_assessment(
        self,
        ranked: tuple[HypothesisAssessment, ...],
    ) -> HypothesisAssessment | None:
        for assessment in ranked:
            if assessment.disposition in {
                HypothesisDisposition.SUPPORTED,
                HypothesisDisposition.TENTATIVE,
            }:
                return assessment
        return None

    def _collect_contradictions(
        self,
        request: ReasoningRequest,
    ) -> tuple[str, ...]:
        propositions: dict[str, set[EvidenceStance]] = {}

        for item in request.evidence:
            key = " ".join(item.proposition.casefold().split())
            propositions.setdefault(key, set()).add(item.stance)

        contradictions = [
            proposition
            for proposition, stances in propositions.items()
            if EvidenceStance.SUPPORTS in stances
            and EvidenceStance.CONTRADICTS in stances
        ]

        return tuple(sorted(contradictions))

    def _collect_missing_information(
        self,
        request: ReasoningRequest,
        assessments: tuple[HypothesisAssessment, ...],
    ) -> tuple[str, ...]:
        missing: set[str] = set()

        for hypothesis in request.hypotheses:
            if not hypothesis.supporting_evidence_ids:
                missing.add(
                    f"Supporting evidence for hypothesis "
                    f"{hypothesis.hypothesis_id}"
                )
            for assumption in hypothesis.assumptions:
                missing.add(f"Validation of assumption: {assumption}")

        for assessment in assessments:
            if assessment.disposition is HypothesisDisposition.INSUFFICIENT:
                missing.add(
                    f"Evidence sufficient to assess hypothesis "
                    f"{assessment.hypothesis_id}"
                )

        return tuple(sorted(missing))

    def _build_planning_recommendation(
        self,
        request: ReasoningRequest,
        selected: HypothesisAssessment | None,
        hypothesis_by_id: dict[str, Hypothesis],
        contradictions: tuple[str, ...],
    ) -> PlanningRecommendation | None:
        if selected is None:
            return None

        hypothesis = hypothesis_by_id[selected.hypothesis_id]
        risks = tuple(
            sorted(
                {
                    *(
                        f"Contradictory evidence: {item}"
                        for item in contradictions
                    ),
                    *(
                        f"Unresolved assumption: {item}"
                        for item in hypothesis.assumptions
                    ),
                    *(
                        ("Low-confidence conclusion",)
                        if selected.confidence < 0.67
                        else ()
                    ),
                }
            )
        )

        return PlanningRecommendation(
            objective=request.goal,
            rationale=(
                f"Selected hypothesis {selected.hypothesis_id}: "
                f"{selected.statement} "
                f"(confidence={selected.confidence:.6f}, "
                f"disposition={selected.disposition.value})."
            ),
            recommended_actions=hypothesis.proposed_actions,
            assumptions=hypothesis.assumptions,
            constraints=request.constraints,
            risks=risks,
        )

    def _build_trace(
        self,
        request: ReasoningRequest,
        assessments: tuple[HypothesisAssessment, ...],
        selected: HypothesisAssessment | None,
    ) -> tuple[ReasoningTraceStep, ...]:
        steps: list[ReasoningTraceStep] = [
            ReasoningTraceStep(
                sequence=1,
                operation="validate_request",
                inputs=(request.request_id,),
                output="valid",
                explanation=(
                    "Identifiers and evidence references were validated."
                ),
            )
        ]

        sequence = 2
        for assessment in assessments:
            steps.append(
                ReasoningTraceStep(
                    sequence=sequence,
                    operation="assess_hypothesis",
                    inputs=(
                        assessment.hypothesis_id,
                        *assessment.supporting_evidence_ids,
                        *assessment.contradicting_evidence_ids,
                    ),
                    output=assessment.disposition.value,
                    explanation=" ".join(assessment.rationale),
                )
            )
            sequence += 1

        steps.append(
            ReasoningTraceStep(
                sequence=sequence,
                operation="select_conclusion",
                inputs=tuple(
                    assessment.hypothesis_id
                    for assessment in assessments
                ),
                output=(
                    selected.hypothesis_id
                    if selected is not None
                    else "none"
                ),
                explanation=(
                    "Hypotheses were ranked by confidence, support, "
                    "contradiction, and stable identifier."
                ),
            )
        )

        return tuple(steps)

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
cd "$PROJECT_ROOT"

if [[ ! -d .git ]]; then
    echo "ERROR: Run from the JARVIS repository root or pass its path."
    exit 1
fi

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X REASONING ENGINE FOUNDATION"
echo "======================================================================"
echo

mkdir -p core/reasoning tests dev/verification docs/architecture

cat > core/reasoning/enums.py <<'JARVIS_PHASE_X_CORE_REASONING_ENUMS_PY'
"""Enumerations for the JARVIS Reasoning Engine foundation."""

from __future__ import annotations

from enum import StrEnum


class EvidenceKind(StrEnum):
    """Origin or semantic class of evidence."""

    FACT = "fact"
    OBSERVATION = "observation"
    TESTIMONY = "testimony"
    DOCUMENT = "document"
    MEASUREMENT = "measurement"
    INFERENCE = "inference"


class EvidenceStance(StrEnum):
    """How an evidence item bears on a proposition or hypothesis."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class HypothesisDisposition(StrEnum):
    """Deterministic assessment state for a candidate hypothesis."""

    SUPPORTED = "supported"
    TENTATIVE = "tentative"
    INSUFFICIENT = "insufficient"
    REJECTED = "rejected"


class ReasoningStatus(StrEnum):
    """Lifecycle state of a reasoning result."""

    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"
JARVIS_PHASE_X_CORE_REASONING_ENUMS_PY

cat > core/reasoning/errors.py <<'JARVIS_PHASE_X_CORE_REASONING_ERRORS_PY'
"""Errors raised by the JARVIS Reasoning Engine foundation."""

from __future__ import annotations


class ReasoningError(RuntimeError):
    """Base error for deterministic reasoning failures."""


class InvalidReasoningRequestError(ReasoningError):
    """Raised when a reasoning request violates its contracts."""


class UnknownEvidenceReferenceError(ReasoningError):
    """Raised when a hypothesis references evidence that does not exist."""


class DuplicateReasoningElementError(ReasoningError):
    """Raised when evidence or hypothesis identifiers are duplicated."""
JARVIS_PHASE_X_CORE_REASONING_ERRORS_PY

cat > core/reasoning/models.py <<'JARVIS_PHASE_X_CORE_REASONING_MODELS_PY'
"""Immutable contracts for the JARVIS Reasoning Engine foundation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from core.reasoning.enums import (
    EvidenceKind,
    EvidenceStance,
    HypothesisDisposition,
    ReasoningStatus,
)


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def _require_probability(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def canonicalize(value: Any) -> Any:
    """Convert reasoning values into stable JSON-compatible structures."""

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "to_dict"):
        return canonicalize(value.to_dict())

    if isinstance(value, Mapping):
        return {
            str(key): canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }

    if isinstance(value, (tuple, list)):
        return [canonicalize(item) for item in value]

    if isinstance(value, set):
        return sorted(canonicalize(item) for item in value)

    return value


def canonical_fingerprint(value: Any) -> str:
    """Return a deterministic SHA-256 fingerprint."""

    encoded = json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """One explicit piece of evidence available to a reasoning session."""

    evidence_id: str
    proposition: str
    stance: EvidenceStance
    source_ref: str
    kind: EvidenceKind = EvidenceKind.FACT
    reliability: float = 1.0
    confidence: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.proposition, "proposition")
        _require_text(self.source_ref, "source_ref")
        _require_probability(self.reliability, "reliability")
        _require_probability(self.confidence, "confidence")

    @property
    def weight(self) -> float:
        return self.reliability * self.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "proposition": self.proposition,
            "stance": self.stance.value,
            "source_ref": self.source_ref,
            "kind": self.kind.value,
            "reliability": self.reliability,
            "confidence": self.confidence,
            "weight": self.weight,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One candidate explanation or course of action to assess."""

    hypothesis_id: str
    statement: str
    supporting_evidence_ids: tuple[str, ...] = ()
    contradicting_evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    proposed_actions: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.hypothesis_id, "hypothesis_id")
        _require_text(self.statement, "statement")

        overlap = set(self.supporting_evidence_ids).intersection(
            self.contradicting_evidence_ids
        )
        if overlap:
            raise ValueError(
                "Evidence cannot both support and contradict the same "
                f"hypothesis: {', '.join(sorted(overlap))}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(
                self.contradicting_evidence_ids
            ),
            "assumptions": list(self.assumptions),
            "proposed_actions": list(self.proposed_actions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    """Complete deterministic input to the Reasoning Engine."""

    request_id: str
    goal: str
    evidence: tuple[EvidenceItem, ...]
    hypotheses: tuple[Hypothesis, ...]
    constraints: tuple[str, ...] = ()
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.goal, "goal")
        if not self.hypotheses:
            raise ValueError("ReasoningRequest must contain at least one hypothesis")

    @property
    def fingerprint(self) -> str:
        return canonical_fingerprint(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "goal": self.goal,
            "evidence": [item.to_dict() for item in self.evidence],
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "constraints": list(self.constraints),
            "context": dict(self.context),
        }


@dataclass(frozen=True, slots=True)
class HypothesisAssessment:
    """Auditable scoring result for one hypothesis."""

    hypothesis_id: str
    statement: str
    support_score: float
    contradiction_score: float
    confidence: float
    disposition: HypothesisDisposition
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement,
            "support_score": self.support_score,
            "contradiction_score": self.contradiction_score,
            "confidence": self.confidence,
            "disposition": self.disposition.value,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(
                self.contradicting_evidence_ids
            ),
            "assumptions": list(self.assumptions),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True, slots=True)
class ReasoningTraceStep:
    """One deterministic, inspectable reasoning operation."""

    sequence: int
    operation: str
    inputs: tuple[str, ...]
    output: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "operation": self.operation,
            "inputs": list(self.inputs),
            "output": self.output,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class PlanningRecommendation:
    """Structured bridge from reasoning into future planning."""

    objective: str
    rationale: str
    recommended_actions: tuple[str, ...]
    assumptions: tuple[str, ...]
    constraints: tuple[str, ...]
    risks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "rationale": self.rationale,
            "recommended_actions": list(self.recommended_actions),
            "assumptions": list(self.assumptions),
            "constraints": list(self.constraints),
            "risks": list(self.risks),
        }


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """Complete output of one deterministic reasoning session."""

    session_id: str
    request_id: str
    request_fingerprint: str
    status: ReasoningStatus
    assessments: tuple[HypothesisAssessment, ...]
    selected_hypothesis_id: str | None
    missing_information: tuple[str, ...]
    contradictions: tuple[str, ...]
    planning_recommendation: PlanningRecommendation | None
    trace: tuple[ReasoningTraceStep, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "request_fingerprint": self.request_fingerprint,
            "status": self.status.value,
            "assessments": [item.to_dict() for item in self.assessments],
            "selected_hypothesis_id": self.selected_hypothesis_id,
            "missing_information": list(self.missing_information),
            "contradictions": list(self.contradictions),
            "planning_recommendation": (
                self.planning_recommendation.to_dict()
                if self.planning_recommendation is not None
                else None
            ),
            "trace": [item.to_dict() for item in self.trace],
            "fingerprint": self.fingerprint,
        }
JARVIS_PHASE_X_CORE_REASONING_MODELS_PY

cat > core/reasoning/confidence.py <<'JARVIS_PHASE_X_CORE_REASONING_CONFIDENCE_PY'
"""Deterministic confidence calculations for JARVIS reasoning."""

from __future__ import annotations

from collections.abc import Iterable

from core.reasoning.enums import HypothesisDisposition
from core.reasoning.models import EvidenceItem


def rounded(value: float) -> float:
    """Normalize floating-point output for stable serialization."""

    return round(value, 6)


def total_weight(items: Iterable[EvidenceItem]) -> float:
    """Return the sum of reliability-adjusted confidence weights."""

    return rounded(sum(item.weight for item in items))


def hypothesis_confidence(
    support_score: float,
    contradiction_score: float,
    assumption_count: int,
) -> float:
    """Calculate conservative confidence for a hypothesis.

    Assumptions add explicit uncertainty rather than being ignored.
    """

    uncertainty = assumption_count * 0.25
    denominator = support_score + contradiction_score + uncertainty

    if denominator == 0.0:
        return 0.0

    return rounded(support_score / denominator)


def classify_disposition(
    support_score: float,
    contradiction_score: float,
    confidence: float,
) -> HypothesisDisposition:
    """Map deterministic scores into an assessment disposition."""

    if contradiction_score > support_score:
        return HypothesisDisposition.REJECTED

    if support_score == 0.0:
        return HypothesisDisposition.INSUFFICIENT

    if confidence >= 0.67:
        return HypothesisDisposition.SUPPORTED

    return HypothesisDisposition.TENTATIVE
JARVIS_PHASE_X_CORE_REASONING_CONFIDENCE_PY

cat > core/reasoning/inference.py <<'JARVIS_PHASE_X_CORE_REASONING_INFERENCE_PY'
"""Deterministic hypothesis assessment for the JARVIS Reasoning Engine."""

from __future__ import annotations

from collections.abc import Mapping

from core.reasoning.confidence import (
    classify_disposition,
    hypothesis_confidence,
    total_weight,
)
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
)


def assess_hypothesis(
    hypothesis: Hypothesis,
    evidence_by_id: Mapping[str, EvidenceItem],
) -> HypothesisAssessment:
    """Assess one hypothesis against explicitly referenced evidence."""

    supporting = tuple(
        evidence_by_id[evidence_id]
        for evidence_id in hypothesis.supporting_evidence_ids
    )
    contradicting = tuple(
        evidence_by_id[evidence_id]
        for evidence_id in hypothesis.contradicting_evidence_ids
    )

    support_score = total_weight(supporting)
    contradiction_score = total_weight(contradicting)
    confidence = hypothesis_confidence(
        support_score=support_score,
        contradiction_score=contradiction_score,
        assumption_count=len(hypothesis.assumptions),
    )
    disposition = classify_disposition(
        support_score=support_score,
        contradiction_score=contradiction_score,
        confidence=confidence,
    )

    rationale = (
        f"Weighted support score: {support_score:.6f}.",
        f"Weighted contradiction score: {contradiction_score:.6f}.",
        f"Unresolved assumptions: {len(hypothesis.assumptions)}.",
        f"Resulting confidence: {confidence:.6f}.",
        f"Disposition: {disposition.value}.",
    )

    return HypothesisAssessment(
        hypothesis_id=hypothesis.hypothesis_id,
        statement=hypothesis.statement,
        support_score=support_score,
        contradiction_score=contradiction_score,
        confidence=confidence,
        disposition=disposition,
        supporting_evidence_ids=hypothesis.supporting_evidence_ids,
        contradicting_evidence_ids=hypothesis.contradicting_evidence_ids,
        assumptions=hypothesis.assumptions,
        rationale=rationale,
    )
JARVIS_PHASE_X_CORE_REASONING_INFERENCE_PY

cat > core/reasoning/service.py <<'JARVIS_PHASE_X_CORE_REASONING_SERVICE_PY'
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
JARVIS_PHASE_X_CORE_REASONING_SERVICE_PY

cat > core/reasoning/__init__.py <<'JARVIS_PHASE_X_CORE_REASONING___INIT___PY'
"""Public interface for the JARVIS Reasoning Engine foundation."""

from core.reasoning.enums import (
    EvidenceKind,
    EvidenceStance,
    HypothesisDisposition,
    ReasoningStatus,
)
from core.reasoning.errors import (
    DuplicateReasoningElementError,
    InvalidReasoningRequestError,
    ReasoningError,
    UnknownEvidenceReferenceError,
)
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
)
from core.reasoning.service import ENGINE_VERSION, ReasoningEngine

__all__ = [
    "ENGINE_VERSION",
    "DuplicateReasoningElementError",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceStance",
    "Hypothesis",
    "HypothesisAssessment",
    "HypothesisDisposition",
    "InvalidReasoningRequestError",
    "PlanningRecommendation",
    "ReasoningEngine",
    "ReasoningError",
    "ReasoningRequest",
    "ReasoningResult",
    "ReasoningStatus",
    "ReasoningTraceStep",
    "UnknownEvidenceReferenceError",
    "canonical_fingerprint",
]
JARVIS_PHASE_X_CORE_REASONING___INIT___PY

cat > tests/test_phase_x_reasoning_foundation.py <<'JARVIS_PHASE_X_TESTS_TEST_PHASE_X_REASONING_FOUNDATION_PY'
"""Tests for the JARVIS Phase X Reasoning Engine foundation."""

from __future__ import annotations

import unittest

from core.reasoning import (
    DuplicateReasoningElementError,
    EvidenceItem,
    EvidenceKind,
    EvidenceStance,
    Hypothesis,
    HypothesisDisposition,
    ReasoningEngine,
    ReasoningRequest,
    ReasoningStatus,
    UnknownEvidenceReferenceError,
)


def build_request() -> ReasoningRequest:
    evidence = (
        EvidenceItem(
            evidence_id="evidence_tests",
            proposition="All verification suites pass",
            stance=EvidenceStance.SUPPORTS,
            source_ref="dev/verify_all.sh",
            kind=EvidenceKind.MEASUREMENT,
            reliability=1.0,
            confidence=0.95,
        ),
        EvidenceItem(
            evidence_id="evidence_architecture",
            proposition="The architecture boundaries are explicit",
            stance=EvidenceStance.SUPPORTS,
            source_ref="docs/architecture",
            kind=EvidenceKind.DOCUMENT,
            reliability=0.9,
            confidence=0.9,
        ),
        EvidenceItem(
            evidence_id="evidence_gap",
            proposition="The reasoning layer is not yet implemented",
            stance=EvidenceStance.CONTRADICTS,
            source_ref="architecture audit",
            kind=EvidenceKind.OBSERVATION,
            reliability=1.0,
            confidence=0.8,
        ),
    )

    hypotheses = (
        Hypothesis(
            hypothesis_id="hypothesis_build_foundation",
            statement=(
                "JARVIS is ready for an additive deterministic "
                "reasoning foundation"
            ),
            supporting_evidence_ids=(
                "evidence_tests",
                "evidence_architecture",
            ),
            assumptions=(
                "Existing public executive interfaces remain stable",
            ),
            proposed_actions=(
                "Create immutable reasoning contracts",
                "Implement deterministic hypothesis assessment",
                "Emit a planning recommendation",
            ),
        ),
        Hypothesis(
            hypothesis_id="hypothesis_do_nothing",
            statement="No reasoning work is required",
            contradicting_evidence_ids=("evidence_gap",),
        ),
    )

    return ReasoningRequest(
        request_id="phase_x_fixture",
        goal="Establish the JARVIS Reasoning Engine foundation",
        evidence=evidence,
        hypotheses=hypotheses,
        constraints=(
            "Do not execute tools",
            "Do not mutate planning or runtime missions",
        ),
        context={"phase": "X"},
    )


class ReasoningFoundationTests(unittest.TestCase):
    def test_selects_best_supported_hypothesis(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertEqual(result.status, ReasoningStatus.COMPLETED)
        self.assertEqual(
            result.selected_hypothesis_id,
            "hypothesis_build_foundation",
        )
        self.assertIsNotNone(result.planning_recommendation)

    def test_rejects_contradicted_hypothesis(self) -> None:
        result = ReasoningEngine().reason(build_request())
        by_id = {
            item.hypothesis_id: item
            for item in result.assessments
        }

        self.assertEqual(
            by_id["hypothesis_do_nothing"].disposition,
            HypothesisDisposition.REJECTED,
        )

    def test_preserves_constraints_for_planning(self) -> None:
        request = build_request()
        result = ReasoningEngine().reason(request)

        assert result.planning_recommendation is not None
        self.assertEqual(
            result.planning_recommendation.constraints,
            request.constraints,
        )

    def test_records_unresolved_assumptions(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertIn(
            (
                "Validation of assumption: Existing public executive "
                "interfaces remain stable"
            ),
            result.missing_information,
        )

    def test_produces_deterministic_fingerprint(self) -> None:
        request = build_request()
        engine = ReasoningEngine()

        first = engine.reason(request)
        second = engine.reason(request)

        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_trace_is_complete_and_ordered(self) -> None:
        result = ReasoningEngine().reason(build_request())

        self.assertEqual(
            [step.sequence for step in result.trace],
            list(range(1, len(result.trace) + 1)),
        )
        self.assertEqual(
            result.trace[0].operation,
            "validate_request",
        )
        self.assertEqual(
            result.trace[-1].operation,
            "select_conclusion",
        )

    def test_rejects_unknown_evidence_reference(self) -> None:
        request = ReasoningRequest(
            request_id="unknown_evidence",
            goal="Test validation",
            evidence=(),
            hypotheses=(
                Hypothesis(
                    hypothesis_id="hypothesis",
                    statement="Unknown evidence should fail",
                    supporting_evidence_ids=("missing",),
                ),
            ),
        )

        with self.assertRaises(UnknownEvidenceReferenceError):
            ReasoningEngine().reason(request)

    def test_rejects_duplicate_identifiers(self) -> None:
        duplicate = EvidenceItem(
            evidence_id="duplicate",
            proposition="A proposition",
            stance=EvidenceStance.SUPPORTS,
            source_ref="fixture",
        )
        request = ReasoningRequest(
            request_id="duplicates",
            goal="Test duplicate validation",
            evidence=(duplicate, duplicate),
            hypotheses=(
                Hypothesis(
                    hypothesis_id="hypothesis",
                    statement="Duplicates should fail",
                    supporting_evidence_ids=("duplicate",),
                ),
            ),
        )

        with self.assertRaises(DuplicateReasoningElementError):
            ReasoningEngine().reason(request)


if __name__ == "__main__":
    unittest.main()
JARVIS_PHASE_X_TESTS_TEST_PHASE_X_REASONING_FOUNDATION_PY

cat > dev/verification/verify_phase_x_reasoning_foundation.py <<'JARVIS_PHASE_X_DEV_VERIFICATION_VERIFY_PHASE_X_REASONING_FOUNDATION_PY'
#!/usr/bin/env python3
"""Structural verification for JARVIS Phase X."""

from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    Path("core/reasoning/__init__.py"),
    Path("core/reasoning/enums.py"),
    Path("core/reasoning/errors.py"),
    Path("core/reasoning/models.py"),
    Path("core/reasoning/confidence.py"),
    Path("core/reasoning/inference.py"),
    Path("core/reasoning/service.py"),
    Path("tests/test_phase_x_reasoning_foundation.py"),
    Path("docs/architecture/reasoning_engine_foundation.md"),
)

FORBIDDEN_IMPORT_PREFIXES = (
    "core.executive.engine",
    "core.executive.store",
    "core.executive.planner",
    "core.executive.director",
    "core.executive.mission_compiler",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)

    return modules


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            failures.append(f"Missing required file: {relative_path}")
            continue

        if path.suffix == ".py":
            try:
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(relative_path),
                )
            except SyntaxError as exc:
                failures.append(
                    f"Syntax error in {relative_path}: {exc}"
                )

    reasoning_root = PROJECT_ROOT / "core" / "reasoning"
    if reasoning_root.is_dir():
        for path in reasoning_root.glob("*.py"):
            for module in imported_modules(path):
                if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    failures.append(
                        f"{path.relative_to(PROJECT_ROOT)} imports "
                        f"forbidden execution dependency {module}"
                    )

    service = reasoning_root / "service.py"
    if service.is_file():
        text = service.read_text(encoding="utf-8")
        for forbidden in (".execute(", "subprocess", "requests.", "openai"):
            if forbidden in text:
                failures.append(
                    f"Reasoning service contains forbidden behavior: "
                    f"{forbidden}"
                )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print("[PASS] Phase X Reasoning Engine structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
JARVIS_PHASE_X_DEV_VERIFICATION_VERIFY_PHASE_X_REASONING_FOUNDATION_PY

cat > dev/verify_phase_x.sh <<'JARVIS_PHASE_X_DEV_VERIFY_PHASE_X_SH'
#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
LOG_FILE="/tmp/jarvis_phase_x_check.log"
PASSED=0
FAILED=0

cd "$PROJECT_ROOT"

pass() {
    printf '[PASS] %s\n' "$1"
    PASSED=$((PASSED + 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAILED=$((FAILED + 1))
}

run_check() {
    local description="$1"
    shift

    if "$@" >"$LOG_FILE" 2>&1; then
        pass "$description"
    else
        fail "$description"
        cat "$LOG_FILE"
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X REASONING ENGINE FOUNDATION"
echo "======================================================================"

run_check \
    "Reasoning package compilation" \
    "$PYTHON_BIN" -m compileall -q core/reasoning

run_check \
    "Reasoning structural boundaries" \
    "$PYTHON_BIN" \
    dev/verification/verify_phase_x_reasoning_foundation.py

run_check \
    "Reasoning foundation unit tests" \
    "$PYTHON_BIN" -m unittest -v \
    tests.test_phase_x_reasoning_foundation

run_check \
    "Stable public reasoning imports" \
    "$PYTHON_BIN" -c '
from core.reasoning import (
    EvidenceItem,
    Hypothesis,
    PlanningRecommendation,
    ReasoningEngine,
    ReasoningRequest,
    ReasoningResult,
)
assert EvidenceItem
assert Hypothesis
assert PlanningRecommendation
assert ReasoningEngine
assert ReasoningRequest
assert ReasoningResult
'

run_check \
    "Deterministic reasoning smoke test" \
    "$PYTHON_BIN" -c '
from tests.test_phase_x_reasoning_foundation import build_request
from core.reasoning import ReasoningEngine
engine = ReasoningEngine()
first = engine.reason(build_request())
second = engine.reason(build_request())
assert first.fingerprint == second.fingerprint
assert first.selected_hypothesis_id == "hypothesis_build_foundation"
assert first.planning_recommendation is not None
'

echo "----------------------------------------------------------------------"
printf 'Checks passed : %d\n' "$PASSED"
printf 'Checks failed : %d\n' "$FAILED"

if [ "$FAILED" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
JARVIS_PHASE_X_DEV_VERIFY_PHASE_X_SH

cat > docs/architecture/reasoning_engine_foundation.md <<'JARVIS_PHASE_X_DOCS_ARCHITECTURE_REASONING_ENGINE_FOUNDATION_MD'
# JARVIS Reasoning Engine Foundation

## Status

Phase X — Implemented foundation.

## Purpose

The Reasoning Engine determines what conclusions are justified by explicit
evidence and converts the selected conclusion into a structured recommendation
that the Planning Engine can later consume.

It does not execute actions and it does not create runtime missions.

## Canonical pipeline

```text
Knowledge and observations
          |
          v
ReasoningRequest
          |
          v
ReasoningEngine
          |
          +-- validates evidence references
          +-- scores support and contradiction
          +-- accounts for assumptions
          +-- ranks hypotheses deterministically
          +-- records missing information
          +-- records contradictions
          +-- emits a justification trace
          |
          v
ReasoningResult
          |
          +-- selected hypothesis
          +-- confidence and disposition
          +-- planning recommendation
          +-- deterministic fingerprint
```

## Phase X contract

Inputs:

- a goal;
- explicit evidence;
- candidate hypotheses;
- assumptions;
- constraints;
- context.

Outputs:

- an assessment for every hypothesis;
- a selected conclusion when justified;
- unresolved information;
- contradictions;
- an immutable reasoning trace;
- a structured planning recommendation;
- a deterministic result fingerprint.

## Confidence model

Each evidence item has:

```text
weight = reliability * confidence
```

For each hypothesis:

```text
support_score = sum(supporting evidence weights)
contradiction_score = sum(contradicting evidence weights)
uncertainty = number_of_assumptions * 0.25

confidence =
    support_score
    / (support_score + contradiction_score + uncertainty)
```

This formula is intentionally simple, inspectable, and replaceable. It is a
constitutional baseline, not a claim that every domain can be reduced to one
universal probability model.

## Dispositions

- `supported`: support exists and confidence is at least 0.67;
- `tentative`: support exists but confidence is below 0.67;
- `insufficient`: no supporting evidence exists;
- `rejected`: contradiction outweighs support.

## Determinism

The same `ReasoningRequest` produces the same:

- hypothesis ordering;
- scores;
- selected conclusion;
- planning recommendation;
- trace;
- fingerprint.

The foundation generates no timestamps and makes no network or model calls.

## Boundaries

Phase X does not:

- retrieve knowledge autonomously;
- invoke an LLM;
- mutate the Knowledge Engine;
- create a canonical planning `Mission`;
- compile a plan;
- execute tools;
- approve actions;
- alter the Executive runtime.

These integrations belong to later controlled phases.

## Next phase

Phase X-B should add a Knowledge Evidence Adapter that converts ranked
Knowledge Engine retrieval results into `EvidenceItem` contracts while
preserving source identity, provenance, retrieval score, and trust state.
JARVIS_PHASE_X_DOCS_ARCHITECTURE_REASONING_ENGINE_FOUNDATION_MD

chmod +x dev/verify_phase_x.sh
chmod +x dev/verification/verify_phase_x_reasoning_foundation.py

echo
echo "Created Phase X files:"
find core/reasoning -maxdepth 1 -type f -print | sort
echo "tests/test_phase_x_reasoning_foundation.py"
echo "dev/verification/verify_phase_x_reasoning_foundation.py"
echo "dev/verify_phase_x.sh"
echo "docs/architecture/reasoning_engine_foundation.md"
echo
echo "Installation complete. Run dev/verify_phase_x.sh next."

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

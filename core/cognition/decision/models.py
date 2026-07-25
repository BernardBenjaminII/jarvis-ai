from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core.cognition.reasoner import ExecutiveReasoningResult
from .enums import DecisionDisposition, DecisionStatus
from .errors import InvalidDecisionRecordError


def _req(value: str, name: str) -> str:
    value = str(value).strip()
    if not value:
        raise InvalidDecisionRecordError(f"{name} must not be empty")
    return value


def _prob(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise InvalidDecisionRecordError(f"{name} must be between 0.0 and 1.0")
    return value


def _canon(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class DecisionAlternative:
    alternative_id: str
    title: str
    rationale: str
    expected_utility: float
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "alternative_id", _req(self.alternative_id, "alternative_id"))
        object.__setattr__(self, "title", _req(self.title, "title"))
        object.__setattr__(self, "rationale", _req(self.rationale, "rationale"))
        object.__setattr__(self, "expected_utility", _prob(self.expected_utility, "expected_utility"))
        object.__setattr__(self, "confidence", _prob(self.confidence, "confidence"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "alternative_id": self.alternative_id,
            "title": self.title,
            "rationale": self.rationale,
            "expected_utility": self.expected_utility,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class DecisionRisk:
    risk_id: str
    description: str
    likelihood: float
    impact: float
    mitigation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_id", _req(self.risk_id, "risk_id"))
        object.__setattr__(self, "description", _req(self.description, "description"))
        object.__setattr__(self, "likelihood", _prob(self.likelihood, "likelihood"))
        object.__setattr__(self, "impact", _prob(self.impact, "impact"))
        object.__setattr__(self, "mitigation", _req(self.mitigation, "mitigation"))

    @property
    def exposure(self) -> float:
        return self.likelihood * self.impact

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "mitigation": self.mitigation,
            "exposure": self.exposure,
        }


@dataclass(frozen=True, slots=True)
class DecisionConstraint:
    constraint_id: str
    description: str
    mandatory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", _req(self.constraint_id, "constraint_id"))
        object.__setattr__(self, "description", _req(self.description, "description"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "description": self.description,
            "mandatory": self.mandatory,
        }


@dataclass(frozen=True, slots=True)
class DecisionSynthesisPolicy:
    minimum_reasoning_confidence: float = 0.40
    minimum_utility: float = 0.35
    maximum_risk_exposure: float = 0.60
    require_selected_hypothesis: bool = True

    def __post_init__(self) -> None:
        for name in ("minimum_reasoning_confidence", "minimum_utility", "maximum_risk_exposure"):
            object.__setattr__(self, name, _prob(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    reasoning_id: str
    situation_id: str
    status: DecisionStatus
    disposition: DecisionDisposition
    selected_alternative_id: str | None
    alternatives: tuple[DecisionAlternative, ...]
    risks: tuple[DecisionRisk, ...]
    constraints: tuple[DecisionConstraint, ...]
    confidence: float
    rationale: str
    required_approvals: tuple[str, ...] = ()
    rollback_criteria: tuple[str, ...] = ()
    expected_outcomes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _req(self.decision_id, "decision_id"))
        object.__setattr__(self, "reasoning_id", _req(self.reasoning_id, "reasoning_id"))
        object.__setattr__(self, "situation_id", _req(self.situation_id, "situation_id"))
        object.__setattr__(self, "confidence", _prob(self.confidence, "confidence"))
        object.__setattr__(self, "rationale", _req(self.rationale, "rationale"))
        alternatives = tuple(sorted(self.alternatives, key=lambda a: a.alternative_id))
        if not alternatives:
            raise InvalidDecisionRecordError("at least one alternative is required")
        object.__setattr__(self, "alternatives", alternatives)
        object.__setattr__(self, "risks", tuple(sorted(self.risks, key=lambda r: r.risk_id)))
        object.__setattr__(self, "constraints", tuple(sorted(self.constraints, key=lambda c: c.constraint_id)))
        object.__setattr__(self, "required_approvals", tuple(sorted(set(self.required_approvals))))
        object.__setattr__(self, "rollback_criteria", tuple(sorted(set(self.rollback_criteria))))
        object.__setattr__(self, "expected_outcomes", tuple(sorted(set(self.expected_outcomes))))
        if self.disposition is DecisionDisposition.RECOMMENDED:
            if self.selected_alternative_id is None:
                raise InvalidDecisionRecordError("recommended decision requires selected alternative")
        elif self.selected_alternative_id is not None:
            raise InvalidDecisionRecordError("non-recommended decision must not select an alternative")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "reasoning_id": self.reasoning_id,
            "situation_id": self.situation_id,
            "status": self.status.value,
            "disposition": self.disposition.value,
            "selected_alternative_id": self.selected_alternative_id,
            "alternatives": [x.to_dict() for x in self.alternatives],
            "risks": [x.to_dict() for x in self.risks],
            "constraints": [x.to_dict() for x in self.constraints],
            "confidence": self.confidence,
            "rationale": self.rationale,
            "required_approvals": list(self.required_approvals),
            "rollback_criteria": list(self.rollback_criteria),
            "expected_outcomes": list(self.expected_outcomes),
        }

    def fingerprint(self) -> str:
        return hashlib.sha256(_canon(self.to_canonical_dict()).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class DecisionQuery:
    situation_id: str | None = None
    disposition: DecisionDisposition | None = None
    minimum_confidence: float | None = None
    limit: int | None = None


def derive_decision_identity(
    reasoning: ExecutiveReasoningResult,
    alternatives: Sequence[DecisionAlternative],
    risks: Sequence[DecisionRisk],
    constraints: Sequence[DecisionConstraint],
    policy: DecisionSynthesisPolicy,
) -> str:
    payload = {
        "reasoning_id": reasoning.reasoning_id,
        "alternatives": [a.to_dict() for a in sorted(alternatives, key=lambda x: x.alternative_id)],
        "risks": [r.to_dict() for r in sorted(risks, key=lambda x: x.risk_id)],
        "constraints": [c.to_dict() for c in sorted(constraints, key=lambda x: x.constraint_id)],
        "policy": {
            "minimum_reasoning_confidence": policy.minimum_reasoning_confidence,
            "minimum_utility": policy.minimum_utility,
            "maximum_risk_exposure": policy.maximum_risk_exposure,
            "require_selected_hypothesis": policy.require_selected_hypothesis,
        },
    }
    return "dec_" + hashlib.sha256(_canon(payload).encode()).hexdigest()

from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

from .enums import CourseOfActionKind, CourseOfActionStatus, GenerationDisposition
from .errors import InvalidCourseOfActionError


def _clean(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidCourseOfActionError(f"{field_name} must be a non-empty string")
    return " ".join(value.split())


def _unit(value: float, field_name: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise InvalidCourseOfActionError(f"{field_name} must be between 0 and 1")
    return round(number, 6)


def _tuple(values: tuple[str, ...] | list[str], field_name: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    normalized = tuple(_clean(v, field_name) for v in values)
    if not allow_empty and not normalized:
        raise InvalidCourseOfActionError(f"{field_name} must not be empty")
    return tuple(dict.fromkeys(normalized))


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

@dataclass(frozen=True, slots=True)
class CourseOfActionTemplate:
    template_id: str
    kind: CourseOfActionKind
    title_pattern: str
    description_pattern: str
    base_utility: float = 0.5
    base_confidence: float = 0.5
    objectives: tuple[str, ...] = ()
    proposed_tasks: tuple[str, ...] = ()
    required_resources: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    expected_outcomes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "template_id", _clean(self.template_id, "template_id"))
        object.__setattr__(self, "title_pattern", _clean(self.title_pattern, "title_pattern"))
        object.__setattr__(self, "description_pattern", _clean(self.description_pattern, "description_pattern"))
        object.__setattr__(self, "base_utility", _unit(self.base_utility, "base_utility"))
        object.__setattr__(self, "base_confidence", _unit(self.base_confidence, "base_confidence"))
        for name in ("objectives", "proposed_tasks", "required_resources", "risks", "constraints", "expected_outcomes", "tags"):
            object.__setattr__(self, name, _tuple(getattr(self, name), name))

@dataclass(frozen=True, slots=True)
class AlternativeGenerationPolicy:
    minimum_reasoning_confidence: float = 0.35
    maximum_candidates: int = 5
    require_hold_alternative: bool = True
    require_contingency_alternative: bool = True
    utility_weight: float = 0.55
    confidence_weight: float = 0.45

    def __post_init__(self) -> None:
        object.__setattr__(self, "minimum_reasoning_confidence", _unit(self.minimum_reasoning_confidence, "minimum_reasoning_confidence"))
        if not 1 <= int(self.maximum_candidates) <= 20:
            raise InvalidCourseOfActionError("maximum_candidates must be between 1 and 20")
        object.__setattr__(self, "maximum_candidates", int(self.maximum_candidates))
        uw = _unit(self.utility_weight, "utility_weight")
        cw = _unit(self.confidence_weight, "confidence_weight")
        if round(uw + cw, 6) != 1.0:
            raise InvalidCourseOfActionError("utility_weight and confidence_weight must sum to 1")
        object.__setattr__(self, "utility_weight", uw)
        object.__setattr__(self, "confidence_weight", cw)

@dataclass(frozen=True, slots=True)
class CourseOfAction:
    coa_id: str
    reasoning_id: str
    selected_hypothesis_id: str
    kind: CourseOfActionKind
    status: CourseOfActionStatus
    title: str
    description: str
    objectives: tuple[str, ...]
    proposed_tasks: tuple[str, ...]
    required_resources: tuple[str, ...]
    risks: tuple[str, ...]
    constraints: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    utility: float
    confidence: float
    rank_score: float
    provenance: tuple[str, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("coa_id", "reasoning_id", "selected_hypothesis_id", "title", "description"):
            object.__setattr__(self, name, _clean(getattr(self, name), name))
        for name in ("objectives", "proposed_tasks", "required_resources", "risks", "constraints", "expected_outcomes", "provenance"):
            object.__setattr__(self, name, _tuple(getattr(self, name), name, allow_empty=(name not in {"objectives", "expected_outcomes"})))
        object.__setattr__(self, "utility", _unit(self.utility, "utility"))
        object.__setattr__(self, "confidence", _unit(self.confidence, "confidence"))
        object.__setattr__(self, "rank_score", _unit(self.rank_score, "rank_score"))
        object.__setattr__(self, "metadata", MappingProxyType(dict(sorted((str(k), str(v)) for k, v in self.metadata.items()))))

    @classmethod
    def derive(cls, **data: Any) -> "CourseOfAction":
        identity_payload = {k: v for k, v in data.items() if k not in {"coa_id", "metadata"}}
        identity_payload = {k: (v.value if hasattr(v, "value") else v) for k, v in identity_payload.items()}
        identity_payload = {k: list(v) if isinstance(v, tuple) else v for k, v in identity_payload.items()}
        coa_id = "coa-" + sha256(_canonical(identity_payload).encode()).hexdigest()[:24]
        return cls(coa_id=coa_id, **data)

    def as_decision_alternative_kwargs(self) -> dict[str, Any]:
        """Return neutral keyword data suitable for an IV-A6.1 adapter."""
        return {
            "alternative_id": self.coa_id,
            "title": self.title,
            "description": self.description,
            "expected_utility": self.utility,
            "confidence": self.confidence,
            "risks": self.risks,
            "constraints": self.constraints,
            "expected_outcomes": self.expected_outcomes,
            "provenance": self.provenance,
        }

@dataclass(frozen=True, slots=True)
class AlternativeGenerationResult:
    generation_id: str
    reasoning_id: str
    disposition: GenerationDisposition
    courses_of_action: tuple[CourseOfAction, ...]
    diagnostics: tuple[str, ...] = ()

    @classmethod
    def derive(cls, reasoning_id: str, disposition: GenerationDisposition, courses_of_action: tuple[CourseOfAction, ...], diagnostics: tuple[str, ...] = ()) -> "AlternativeGenerationResult":
        payload = {"reasoning_id": reasoning_id, "disposition": disposition.value, "coa_ids": [c.coa_id for c in courses_of_action], "diagnostics": list(diagnostics)}
        generation_id = "coag-" + sha256(_canonical(payload).encode()).hexdigest()[:24]
        return cls(generation_id, reasoning_id, disposition, courses_of_action, diagnostics)

__all__ = ["CourseOfActionTemplate", "AlternativeGenerationPolicy", "CourseOfAction", "AlternativeGenerationResult"]

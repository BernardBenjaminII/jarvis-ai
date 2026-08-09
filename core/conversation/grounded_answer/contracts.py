from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.retrieval.grounded_answer import (
    GroundedAnswer,
    GroundedAnswerPlan,
)
from core.retrieval.qualification import QualificationResult


def _freeze(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class GroundedAnswerRuntimeContext:
    request_id: str
    session_id: str
    operator_input: str
    mode: str = "full"
    channel: str = "text"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "operator_input": self.operator_input,
            "mode": self.mode,
            "channel": self.channel,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class GroundedAnswerExecutionRequest:
    context: GroundedAnswerRuntimeContext
    qualification: QualificationResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "qualification": self.qualification.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class GroundedAnswerExecutionResponse:
    plan: GroundedAnswerPlan
    answer: GroundedAnswer | None
    synthesis_invoked: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def state(self) -> str:
        return self.plan.state.value

    @property
    def confidence(self) -> float:
        return self.plan.confidence

    @property
    def citations(self) -> tuple:
        return self.plan.citations

    @property
    def conflicts(self) -> tuple:
        return self.plan.conflicts

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "answer": None if self.answer is None else self.answer.to_dict(),
            "synthesis_invoked": self.synthesis_invoked,
            "state": self.state,
            "confidence": self.confidence,
            "citations": [item.to_dict() for item in self.citations],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "metadata": dict(self.metadata),
        }

from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from .classification import FailureClassification, FailureSeverity

def _freeze(value):
    return MappingProxyType(dict(value or {}))

@dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    expected_state: str | None = None
    minimum_confidence: float | None = None
    maximum_confidence: float | None = None
    minimum_accepted_evidence: int | None = None
    maximum_accepted_evidence: int | None = None
    minimum_rejected_evidence: int | None = None
    require_recommendation: bool | None = None
    require_citations: bool | None = None
    require_answer_text: bool = True
    forbidden_phrases: tuple[str, ...] = ()
    required_phrases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_state": self.expected_state,
            "minimum_confidence": self.minimum_confidence,
            "maximum_confidence": self.maximum_confidence,
            "minimum_accepted_evidence": self.minimum_accepted_evidence,
            "maximum_accepted_evidence": self.maximum_accepted_evidence,
            "minimum_rejected_evidence": self.minimum_rejected_evidence,
            "require_recommendation": self.require_recommendation,
            "require_citations": self.require_citations,
            "require_answer_text": self.require_answer_text,
            "forbidden_phrases": list(self.forbidden_phrases),
            "required_phrases": list(self.required_phrases),
        }

@dataclass(frozen=True, slots=True)
class AcceptanceTestCase:
    test_id: str
    domain: str
    name: str
    prompt: str
    expected: ExpectedOutcome
    mode: str = "full"
    timeout_seconds: float = 120.0
    severity_on_failure: FailureSeverity = FailureSeverity.S3
    classification_on_failure: FailureClassification = FailureClassification.UNKNOWN
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self):
        return {
            "test_id": self.test_id, "domain": self.domain, "name": self.name,
            "prompt": self.prompt, "expected": self.expected.to_dict(),
            "mode": self.mode, "timeout_seconds": self.timeout_seconds,
            "severity_on_failure": self.severity_on_failure.value,
            "classification_on_failure": self.classification_on_failure.value,
            "metadata": dict(self.metadata),
        }

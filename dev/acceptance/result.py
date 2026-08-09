from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from .classification import FailureClassification, FailureSeverity

def _freeze(value):
    return MappingProxyType(dict(value or {}))

class AcceptanceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"

@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    run_id: str
    test_id: str
    domain: str
    status: AcceptanceStatus
    started_at: str
    completed_at: str
    duration_ms: float
    answer: str
    observed_state: str | None
    confidence: float | None
    accepted_evidence: int | None
    rejected_evidence: int | None
    citation_count: int | None
    conflict_count: int | None
    recommendation: str | None
    assertions: tuple[dict[str, Any], ...] = ()
    classification: FailureClassification | None = None
    severity: FailureSeverity | None = None
    error: str | None = None
    telemetry: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "assertions", tuple(dict(x) for x in self.assertions))
        object.__setattr__(self, "telemetry", _freeze(self.telemetry))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def passed(self):
        return self.status is AcceptanceStatus.PASS

    def to_dict(self):
        return {
            "run_id": self.run_id, "test_id": self.test_id, "domain": self.domain,
            "status": self.status.value, "started_at": self.started_at,
            "completed_at": self.completed_at, "duration_ms": self.duration_ms,
            "answer": self.answer, "observed_state": self.observed_state,
            "confidence": self.confidence, "accepted_evidence": self.accepted_evidence,
            "rejected_evidence": self.rejected_evidence,
            "citation_count": self.citation_count,
            "conflict_count": self.conflict_count,
            "recommendation": self.recommendation,
            "assertions": [dict(x) for x in self.assertions],
            "classification": None if self.classification is None else self.classification.value,
            "severity": None if self.severity is None else self.severity.value,
            "error": self.error, "telemetry": dict(self.telemetry),
            "metadata": dict(self.metadata),
        }

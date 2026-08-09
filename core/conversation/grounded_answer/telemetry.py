from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from types import MappingProxyType
from typing import Any, Mapping

def _freeze(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))

@dataclass(frozen=True, slots=True)
class GroundedAnswerTelemetry:
    generated_at: str
    request_id: str
    session_id: str
    query: str
    state: str
    confidence: float
    accepted_evidence: int
    rejected_evidence: int
    citation_count: int
    conflict_count: int
    uncertainty_note: str
    recommended_action: str | None
    citations: tuple[dict[str, Any], ...] = ()
    conflicts: tuple[dict[str, Any], ...] = ()
    rank_scores: tuple[float, ...] = ()
    source_paths: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "citations", tuple(dict(x) for x in self.citations))
        object.__setattr__(self, "conflicts", tuple(dict(x) for x in self.conflicts))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self):
        return {
            "available": True, "generated_at": self.generated_at,
            "request_id": self.request_id, "session_id": self.session_id,
            "query": self.query, "state": self.state, "confidence": self.confidence,
            "accepted_evidence": self.accepted_evidence,
            "rejected_evidence": self.rejected_evidence,
            "citation_count": self.citation_count, "conflict_count": self.conflict_count,
            "uncertainty_note": self.uncertainty_note,
            "recommended_action": self.recommended_action,
            "citations": [dict(x) for x in self.citations],
            "conflicts": [dict(x) for x in self.conflicts],
            "rank_scores": list(self.rank_scores),
            "source_paths": list(self.source_paths),
            "metadata": dict(self.metadata),
        }

class GroundedAnswerTelemetryStore:
    def __init__(self):
        self._lock=RLock(); self._latest=None
    def publish(self, snapshot):
        with self._lock: self._latest=snapshot
    def latest(self):
        with self._lock: return self._latest
    def clear(self):
        with self._lock: self._latest=None
    def projection(self):
        x=self.latest()
        if x is None:
            return {"available":False,"state":"unavailable","confidence":0.0,
                    "accepted_evidence":0,"rejected_evidence":0,
                    "citation_count":0,"conflict_count":0,
                    "citations":[],"conflicts":[],"rank_scores":[],"source_paths":[],
                    "uncertainty_note":"No grounded-answer request has completed.",
                    "recommended_action":None}
        return x.to_dict()

_DEFAULT_STORE=GroundedAnswerTelemetryStore()

def get_grounded_answer_telemetry_store():
    return _DEFAULT_STORE

def publish_grounded_answer_telemetry(*, runtime_request, qualification, response):
    plan=response.plan; context=runtime_request.context
    snapshot=GroundedAnswerTelemetry(
        generated_at=datetime.now(timezone.utc).isoformat(),
        request_id=context.request_id, session_id=context.session_id,
        query=context.operator_input, state=plan.state.value,
        confidence=plan.confidence, accepted_evidence=len(qualification.accepted),
        rejected_evidence=len(qualification.rejected),
        citation_count=len(plan.citations), conflict_count=len(plan.conflicts),
        uncertainty_note=plan.uncertainty_note,
        recommended_action=plan.recommended_action,
        citations=tuple(x.to_dict() for x in plan.citations),
        conflicts=tuple(x.to_dict() for x in plan.conflicts),
        rank_scores=tuple(x.rank_score for x in plan.ranked_evidence),
        source_paths=tuple(x.source_path for x in plan.ranked_evidence),
        metadata={"synthesis_invoked":response.synthesis_invoked,
                  "mode":context.mode,"channel":context.channel},
    )
    get_grounded_answer_telemetry_store().publish(snapshot)
    return snapshot

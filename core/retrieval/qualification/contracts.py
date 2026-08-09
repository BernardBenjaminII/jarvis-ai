from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from .enums import QualificationDecision

def _freeze(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))

def _unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    source_id: str
    source_path: str
    title: str
    subject: str
    excerpt: str
    backend: str
    retrieval_score: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieval_score", _unit(self.retrieval_score))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_path": self.source_path,
            "title": self.title,
            "subject": self.subject,
            "excerpt": self.excerpt,
            "backend": self.backend,
            "retrieval_score": self.retrieval_score,
            "metadata": dict(self.metadata),
        }

@dataclass(frozen=True, slots=True)
class QualificationScore:
    lexical: float = 0.0
    semantic: float = 0.0
    phrase: float = 0.0
    entity: float = 0.0
    subject: float = 0.0
    provenance: float = 0.0
    final: float = 0.0

    def __post_init__(self) -> None:
        for name in ("lexical","semantic","phrase","entity","subject","provenance","final"):
            object.__setattr__(self, name, _unit(getattr(self, name)))

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in (
            "lexical","semantic","phrase","entity","subject","provenance","final"
        )}

@dataclass(frozen=True, slots=True)
class QualifiedEvidence:
    candidate: EvidenceCandidate
    score: QualificationScore
    decision: QualificationDecision
    explanation: str = ""

    @property
    def accepted(self) -> bool:
        return self.decision is QualificationDecision.ACCEPTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "score": self.score.to_dict(),
            "decision": self.decision.value,
            "accepted": self.accepted,
            "explanation": self.explanation,
        }

@dataclass(frozen=True, slots=True)
class QualificationResult:
    accepted: tuple[QualifiedEvidence, ...] = ()
    rejected: tuple[QualifiedEvidence, ...] = ()
    threshold: float = 0.0
    runtime_statistics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted", tuple(self.accepted))
        object.__setattr__(self, "rejected", tuple(self.rejected))
        object.__setattr__(self, "threshold", _unit(self.threshold))
        object.__setattr__(self, "runtime_statistics", _freeze(self.runtime_statistics))
        if any(not item.accepted for item in self.accepted):
            raise ValueError("accepted contains rejected evidence")
        if any(item.accepted for item in self.rejected):
            raise ValueError("rejected contains accepted evidence")

    @property
    def total_candidates(self) -> int:
        return len(self.accepted) + len(self.rejected)

    @property
    def has_accepted_evidence(self) -> bool:
        return bool(self.accepted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": [x.to_dict() for x in self.accepted],
            "rejected": [x.to_dict() for x in self.rejected],
            "threshold": self.threshold,
            "runtime_statistics": dict(self.runtime_statistics),
            "total_candidates": self.total_candidates,
            "has_accepted_evidence": self.has_accepted_evidence,
        }

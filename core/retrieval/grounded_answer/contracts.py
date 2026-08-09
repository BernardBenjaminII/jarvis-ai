from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .enums import AnswerKnowledgeState, ConflictSeverity

def _unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

@dataclass(frozen=True, slots=True)
class RankedEvidence:
    evidence_id: str
    source_id: str
    source_path: str
    title: str
    subject: str
    excerpt: str
    relevance: float
    retrieval_score: float
    rank_score: float

    def __post_init__(self):
        for name in ("relevance", "retrieval_score", "rank_score"):
            object.__setattr__(self, name, _unit(getattr(self, name)))

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__slots__}

@dataclass(frozen=True, slots=True)
class AnswerCitation:
    citation_id: str
    evidence_id: str
    source_id: str
    source_path: str
    title: str
    excerpt: str
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__slots__}

@dataclass(frozen=True, slots=True)
class AnswerConflict:
    conflict_id: str
    left_evidence_id: str
    right_evidence_id: str
    severity: ConflictSeverity
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "left_evidence_id": self.left_evidence_id,
            "right_evidence_id": self.right_evidence_id,
            "severity": self.severity.value,
            "reason": self.reason,
        }

@dataclass(frozen=True, slots=True)
class GroundedAnswerPlan:
    query: str
    state: AnswerKnowledgeState
    confidence: float
    ranked_evidence: tuple[RankedEvidence, ...]
    citations: tuple[AnswerCitation, ...]
    conflicts: tuple[AnswerConflict, ...]
    synthesis_prompt: str
    uncertainty_note: str
    recommended_action: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "confidence", _unit(self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "state": self.state.value,
            "confidence": self.confidence,
            "ranked_evidence": [x.to_dict() for x in self.ranked_evidence],
            "citations": [x.to_dict() for x in self.citations],
            "conflicts": [x.to_dict() for x in self.conflicts],
            "synthesis_prompt": self.synthesis_prompt,
            "uncertainty_note": self.uncertainty_note,
            "recommended_action": self.recommended_action,
        }

@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    answer: str
    state: AnswerKnowledgeState
    confidence: float
    citations: tuple[AnswerCitation, ...]
    conflicts: tuple[AnswerConflict, ...]
    uncertainty_note: str
    recommended_action: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "confidence", _unit(self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "state": self.state.value,
            "confidence": self.confidence,
            "citations": [x.to_dict() for x in self.citations],
            "conflicts": [x.to_dict() for x in self.conflicts],
            "uncertainty_note": self.uncertainty_note,
            "recommended_action": self.recommended_action,
        }

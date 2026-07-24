"""Immutable C-5 executive knowledge-awareness contracts."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class KnowledgeCoverage:
    objective_id: str
    query: str
    evidence_count: int
    source_count: int
    average_weight: float
    coverage: float
    maturity: str
    answerability: str
    gaps: tuple[str, ...] = ()
    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id, "query": self.query,
            "evidence_count": self.evidence_count, "source_count": self.source_count,
            "average_weight": self.average_weight, "coverage": self.coverage,
            "maturity": self.maturity, "answerability": self.answerability,
            "gaps": list(self.gaps),
        }

@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    objective_id: str
    status: str
    selected_hypothesis_id: str | None
    confidence: float
    contradiction_count: int
    missing_information: tuple[str, ...]
    reasoning_fingerprint: str | None
    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id, "status": self.status,
            "selected_hypothesis_id": self.selected_hypothesis_id,
            "confidence": self.confidence,
            "contradiction_count": self.contradiction_count,
            "missing_information": list(self.missing_information),
            "reasoning_fingerprint": self.reasoning_fingerprint,
        }

@dataclass(frozen=True, slots=True)
class ResearchRecommendation:
    objective_id: str
    query: str
    priority: str
    reason: str
    recommended_action: str
    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id, "query": self.query,
            "priority": self.priority, "reason": self.reason,
            "recommended_action": self.recommended_action,
        }

@dataclass(frozen=True, slots=True)
class ExecutiveKnowledgeState:
    status: str
    answerability: str
    confidence: float
    coverage: tuple[KnowledgeCoverage, ...]
    assessments: tuple[EvidenceAssessment, ...]
    research_queue: tuple[ResearchRecommendation, ...]
    evidence_count: int
    source_count: int
    contradiction_count: int
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status, "answerability": self.answerability,
            "confidence": self.confidence,
            "coverage": [x.to_dict() for x in self.coverage],
            "assessments": [x.to_dict() for x in self.assessments],
            "research_queue": [x.to_dict() for x in self.research_queue],
            "evidence_count": self.evidence_count, "source_count": self.source_count,
            "contradiction_count": self.contradiction_count,
        }
    def synthesis_input(self, operator_input: str) -> str:
        lines=[operator_input, "", "JARVIS EXECUTIVE KNOWLEDGE STATE:",
               f"Status: {self.status}", f"Answerability: {self.answerability}",
               f"Confidence: {self.confidence:.3f}",
               f"Evidence: {self.evidence_count}", f"Sources: {self.source_count}",
               f"Contradictions: {self.contradiction_count}"]
        if self.research_queue:
            lines.append("Knowledge gaps requiring acquisition:")
            lines.extend(f"- {x.query}: {x.reason}" for x in self.research_queue)
        return "\n".join(lines)

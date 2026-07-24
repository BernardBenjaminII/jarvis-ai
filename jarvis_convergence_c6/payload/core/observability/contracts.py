"""Immutable C-6 Executive observability contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TransparencyEvent:
    sequence: int
    stage: str
    status: str
    summary: str
    data: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "stage": self.stage,
            "status": self.status,
            "summary": self.summary,
            "data": dict(self.data),
        }


@dataclass(frozen=True, slots=True)
class MissionTransparencySnapshot:
    request_id: str
    session_id: str
    objective_count: int
    mission_count: int
    directors: tuple[str, ...]
    current_stage: str
    status: str
    confidence: float | None
    answerability: str | None
    evidence_count: int
    knowledge_gap_count: int
    contradiction_count: int
    events: tuple[TransparencyEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "objective_count": self.objective_count,
            "mission_count": self.mission_count,
            "directors": list(self.directors),
            "current_stage": self.current_stage,
            "status": self.status,
            "confidence": self.confidence,
            "answerability": self.answerability,
            "evidence_count": self.evidence_count,
            "knowledge_gap_count": self.knowledge_gap_count,
            "contradiction_count": self.contradiction_count,
            "events": [event.to_dict() for event in self.events],
        }

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def required_text(value: object, name: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{name} is required")
    return result


@dataclass(frozen=True, slots=True)
class WorkspaceConversationRequest:
    question: str
    session_id: str | None = None
    mode: str = "knowledge"
    context: Mapping[str, Any] = field(
        default_factory=lambda: {"workspace": "knowledge"}
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "question", required_text(self.question, "question"))
        object.__setattr__(self, "mode", required_text(self.mode, "mode"))
        object.__setattr__(
            self,
            "session_id",
            str(self.session_id).strip() if self.session_id else None,
        )
        object.__setattr__(self, "context", dict(self.context or {}))

    def runtime_kwargs(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "question": self.question,
            "mode": self.mode,
        }
        if self.session_id:
            values["session_id"] = self.session_id
        return values


@dataclass(frozen=True, slots=True)
class WorkspaceConversationResponse:
    status: str
    answer: str
    session_id: str | None
    confidence: float | None
    latency_ms: int
    sources: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    activity: tuple[dict[str, str], ...] = ()
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "session_id": self.session_id,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "sources": list(self.sources),
            "evidence": list(self.evidence),
            "activity": list(self.activity),
            "error": self.error,
        }

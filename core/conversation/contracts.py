"""Stable contracts for JARVIS executive conversation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationRole(str, Enum):
    OPERATOR = "operator"
    JARVIS = "jarvis"
    SYSTEM = "system"


class ConversationState(str, Enum):
    READY = "ready"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CompiledObjective:
    objective_id: str
    text: str
    ordinal: int
    routing_hints: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["routing_hints"] = list(self.routing_hints)
        return data


@dataclass(frozen=True, slots=True)
class ExecutiveRequestContext:
    request_id: str
    session_id: str
    operator_input: str
    mode: str = "full"
    channel: str = "text"
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    objectives: tuple[CompiledObjective, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        operator_input: str,
        session_id: str | None = None,
        mode: str = "full",
        channel: str = "text",
        metadata: dict[str, Any] | None = None,
        objectives: tuple[CompiledObjective, ...] = (),
    ) -> "ExecutiveRequestContext":
        return cls(
            request_id=uuid4().hex,
            session_id=session_id or uuid4().hex,
            operator_input=operator_input.strip(),
            mode=mode,
            channel=channel,
            metadata=dict(metadata or {}),
            objectives=objectives,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "operator_input": self.operator_input,
            "mode": self.mode,
            "channel": self.channel,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "objectives": [item.to_dict() for item in self.objectives],
        }


@dataclass(frozen=True, slots=True)
class ConversationTraceEvent:
    stage: str
    status: str
    detail: str
    timestamp: str = field(default_factory=utc_now)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    message_id: str
    session_id: str
    role: ConversationRole
    content: str
    created_at: str = field(default_factory=utc_now)
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        role: ConversationRole,
        content: str,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ConversationMessage":
        return cls(
            message_id=uuid4().hex,
            session_id=session_id,
            role=role,
            content=content,
            request_id=request_id,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        return data


@dataclass(frozen=True, slots=True)
class ExecutiveConversationResponse:
    request_id: str
    session_id: str
    state: ConversationState
    answer: str
    objectives: tuple[CompiledObjective, ...]
    trace: tuple[ConversationTraceEvent, ...]
    created_at: str = field(default_factory=utc_now)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "answer": self.answer,
            "objectives": [item.to_dict() for item in self.objectives],
            "trace": [item.to_dict() for item in self.trace],
            "created_at": self.created_at,
            "error": self.error,
            "metadata": dict(self.metadata),
        }

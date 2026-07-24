"""Domain models for the JARVIS Gen 2 mission system."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MissionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass(slots=True)
class MissionTask:
    title: str
    director: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    routing_evidence: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionTask":
        values = dict(data)
        values["status"] = TaskStatus(values.get("status", TaskStatus.PENDING.value))
        values.setdefault("required_capabilities", [])
        values.setdefault("routing_evidence", {})
        return cls(**values)


@dataclass(slots=True)
class Mission:
    objective: str
    context: dict[str, Any] = field(default_factory=dict)
    mission_id: str = field(default_factory=lambda: uuid4().hex)
    status: MissionStatus = MissionStatus.DRAFT
    tasks: list[MissionTask] = field(default_factory=list)
    summary: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "context": self.context,
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.tasks],
            "summary": self.summary,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Mission":
        values = dict(data)
        values["status"] = MissionStatus(values.get("status", MissionStatus.DRAFT.value))
        values["tasks"] = [MissionTask.from_dict(task) for task in values.get("tasks", [])]
        return cls(**values)


@dataclass(slots=True)
class TaskExecutionResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

"""Immutable data contracts for Genesis VI-A1 executive cognition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .enums import (
    AttentionReason,
    CognitiveCycleStatus,
    CognitiveEventKind,
    CognitiveState,
    MemoryEntryKind,
)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return a shallow immutable mapping with deterministic key ordering."""

    if not value:
        return MappingProxyType({})

    ordered = {
        str(key): value[key]
        for key in sorted(value, key=lambda item: str(item))
    }
    return MappingProxyType(ordered)


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    """An immutable item held in executive working memory."""

    entry_id: str
    kind: MemoryEntryKind
    content: str
    importance: float = 0.5
    confidence: float = 1.0
    source: str = "executive"
    created_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError("entry_id must not be empty")
        if not self.content.strip():
            raise ValueError("content must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class AttentionCandidate:
    """An immutable subject requesting finite executive attention."""

    candidate_id: str
    subject: str
    reasons: Tuple[AttentionReason, ...]
    mission_criticality: float = 0.0
    safety_impact: float = 0.0
    authority_impact: float = 0.0
    uncertainty: float = 0.0
    novelty: float = 0.0
    dependency_pressure: float = 0.0
    user_priority: float = 0.0
    failure_pressure: float = 0.0
    deadline_pressure: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        if not self.subject.strip():
            raise ValueError("subject must not be empty")
        if not self.reasons:
            raise ValueError("at least one attention reason is required")

        factors = (
            self.mission_criticality,
            self.safety_impact,
            self.authority_impact,
            self.uncertainty,
            self.novelty,
            self.dependency_pressure,
            self.user_priority,
            self.failure_pressure,
            self.deadline_pressure,
        )
        if any(not 0.0 <= value <= 1.0 for value in factors):
            raise ValueError("attention factors must be between 0.0 and 1.0")

        object.__setattr__(
            self,
            "reasons",
            tuple(sorted(set(self.reasons), key=lambda reason: reason.value)),
        )
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class AttentionAllocation:
    """A deterministic attention allocation record."""

    candidate_id: str
    subject: str
    score: float
    rank: int
    reasons: Tuple[AttentionReason, ...]
    explanation: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        if not self.subject.strip():
            raise ValueError("subject must not be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        if self.rank < 1:
            raise ValueError("rank must be at least 1")
        if not self.explanation.strip():
            raise ValueError("explanation must not be empty")

        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class StateTransition:
    """An immutable cognitive-state transition record."""

    sequence: int
    previous_state: CognitiveState
    next_state: CognitiveState
    reason: str
    occurred_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("sequence must be at least 1")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class CognitiveEvent:
    """An immutable event emitted by executive cognition."""

    sequence: int
    kind: CognitiveEventKind
    message: str
    state: CognitiveState
    occurred_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("sequence must be at least 1")
        if not self.message.strip():
            raise ValueError("message must not be empty")

        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class ExecutiveContext:
    """Authoritative immutable snapshot of an executive cognition lifecycle."""

    cycle_id: str
    mission_id: str
    goal: str
    state: CognitiveState
    status: CognitiveCycleStatus
    authority: str
    objective_id: str | None = None
    task_id: str | None = None
    constraints: Tuple[str, ...] = ()
    working_memory: Tuple[MemoryEntry, ...] = ()
    attention: Tuple[AttentionAllocation, ...] = ()
    transitions: Tuple[StateTransition, ...] = ()
    events: Tuple[CognitiveEvent, ...] = ()
    notes: Tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cycle_id.strip():
            raise ValueError("cycle_id must not be empty")
        if not self.mission_id.strip():
            raise ValueError("mission_id must not be empty")
        if not self.goal.strip():
            raise ValueError("goal must not be empty")
        if not self.authority.strip():
            raise ValueError("authority must not be empty")

        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "working_memory", tuple(self.working_memory))
        object.__setattr__(self, "attention", tuple(self.attention))
        object.__setattr__(self, "transitions", tuple(self.transitions))
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "notes", tuple(self.notes))
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))

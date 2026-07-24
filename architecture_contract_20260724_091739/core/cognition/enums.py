"""Enumerations for the Genesis VI-A1 executive cognition foundation."""

from __future__ import annotations

from enum import Enum


class CognitiveState(str, Enum):
    """Canonical states of an executive cognition lifecycle."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    OBSERVING = "observing"
    ATTENDING = "attending"
    RETRIEVING = "retrieving"
    REASONING = "reasoning"
    EVALUATING = "evaluating"
    PLANNING = "planning"
    AWAITING_AUTHORITY = "awaiting_authority"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class CognitiveCycleStatus(str, Enum):
    """Lifecycle status of an executive cognition cycle."""

    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class MemoryEntryKind(str, Enum):
    """Kinds of information admitted into executive working memory."""

    GOAL = "goal"
    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    FACT = "fact"
    ASSUMPTION = "assumption"
    CONSTRAINT = "constraint"
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    DECISION = "decision"
    PLAN = "plan"
    RESULT = "result"
    REFLECTION = "reflection"


class AttentionReason(str, Enum):
    """Reasons an item may deserve executive attention."""

    MISSION_CRITICALITY = "mission_criticality"
    SAFETY = "safety"
    AUTHORITY = "authority"
    UNCERTAINTY = "uncertainty"
    NOVELTY = "novelty"
    DEPENDENCY = "dependency"
    USER_PRIORITY = "user_priority"
    FAILURE = "failure"
    DEADLINE = "deadline"


class CognitiveEventKind(str, Enum):
    """Canonical events emitted by executive cognition."""

    CONTEXT_CREATED = "context_created"
    STATE_CHANGED = "state_changed"
    MEMORY_ADMITTED = "memory_admitted"
    MEMORY_EVICTED = "memory_evicted"
    ATTENTION_ALLOCATED = "attention_allocated"
    NOTE_RECORDED = "note_recorded"
    CYCLE_COMPLETED = "cycle_completed"
    CYCLE_FAILED = "cycle_failed"
    CYCLE_SUSPENDED = "cycle_suspended"

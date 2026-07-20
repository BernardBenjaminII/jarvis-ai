"""Canonical enumerations for the deterministic planning engine."""

from __future__ import annotations

from enum import StrEnum


class WorkItemKind(StrEnum):
    """Canonical mission-hierarchy item types."""

    MISSION = "mission"
    OBJECTIVE = "objective"
    TASK = "task"
    ACTIVITY = "activity"
    COMMAND = "command"


class WorkItemState(StrEnum):
    """Observed execution state supplied to the planning engine."""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ReadinessState(StrEnum):
    """Derived readiness determined by planning analysis."""

    READY = "ready"
    BLOCKED = "blocked"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    TERMINAL = "terminal"


class BlockerType(StrEnum):
    """Canonical reasons that prevent work from becoming runnable."""

    DEPENDENCY = "dependency"
    PARENT = "parent"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    CONSTRAINT = "constraint"
    EXECUTION_FAILURE = "execution_failure"
    UNKNOWN_REFERENCE = "unknown_reference"


class RecommendationType(StrEnum):
    """Planning-engine recommendation categories."""

    EXECUTE = "execute"
    CONTINUE = "continue"
    REQUEST_AUTHORIZATION = "request_authorization"
    RESOLVE_BLOCKER = "resolve_blocker"
    REPLAN = "replan"
    COMPLETE = "complete"
    HALT = "halt"
    NONE = "none"


class ConfidenceBand(StrEnum):
    """Human-readable interpretation of recommendation confidence."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TraceSeverity(StrEnum):
    """Severity used by explainable decision traces."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class PlanningPolicy(StrEnum):
    """Deterministic strategy used to rank runnable work."""

    BALANCED = "balanced"
    PRIORITY_FIRST = "priority_first"
    SHORTEST_PATH = "shortest_path"
    CRITICAL_PATH = "critical_path"
    RISK_AVERSE = "risk_averse"

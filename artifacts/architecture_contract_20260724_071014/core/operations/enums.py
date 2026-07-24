"""Enumerations for the JARVIS Operations interface."""

from __future__ import annotations

from enum import Enum


class OperationalState(str, Enum):
    """Top-level operational state."""

    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    PAUSED = "paused"
    FAILED = "failed"
    STOPPED = "stopped"


class ExecutiveState(str, Enum):
    """
    Public Executive runtime state.

    This describes what the Executive Operating System is currently
    doing—not the health of the system.
    """

    INITIALIZING = "initializing"

    READY = "ready"

    OBSERVING = "observing"

    REASONING = "reasoning"

    PLANNING = "planning"

    EXECUTING = "executing"

    WAITING = "waiting"

    PAUSED = "paused"

    DEGRADED = "degraded"

    FAILED = "failed"

    STOPPED = "stopped"


class HealthState(str, Enum):
    """Health of an individual component."""

    HEALTHY = "healthy"

    DEGRADED = "degraded"

    UNAVAILABLE = "unavailable"

    UNKNOWN = "unknown"


class MissionState(str, Enum):
    """Externally visible mission state."""

    PLANNED = "planned"

    ACTIVE = "active"

    PAUSED = "paused"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"


class ObjectiveState(str, Enum):
    """Externally visible objective state."""

    PENDING = "pending"

    ACTIVE = "active"

    BLOCKED = "blocked"

    COMPLETED = "completed"

    FAILED = "failed"


class ActivityState(str, Enum):
    """Externally visible activity state."""

    QUEUED = "queued"

    RUNNING = "running"

    SUCCEEDED = "succeeded"

    FAILED = "failed"

    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    """Operational alert severity."""

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


class EventKind(str, Enum):
    """Canonical Operations event names."""

    MISSION_STARTED = "MissionStarted"

    MISSION_COMPLETED = "MissionCompleted"

    OBSERVATION_CREATED = "ObservationCreated"

    EVIDENCE_VALIDATED = "EvidenceValidated"

    REASONING_STARTED = "ReasoningStarted"

    REASONING_COMPLETED = "ReasoningCompleted"

    KNOWLEDGE_ASSIMILATED = "KnowledgeAssimilated"

    CHECKPOINT_CREATED = "CheckpointCreated"

    EXECUTIVE_RECOVERED = "ExecutiveRecovered"

    SYSTEM_HEALTH_CHANGED = "SystemHealthChanged"

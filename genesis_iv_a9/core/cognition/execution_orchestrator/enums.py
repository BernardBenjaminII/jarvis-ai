from __future__ import annotations

from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    ROLLBACK_PENDING = "rollback_pending"
    ROLLED_BACK = "rolled_back"


class MissionExecutionStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class DispatchMode(str, Enum):
    HUMAN = "human"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class ObservationKind(str, Enum):
    EXECUTION_STARTED = "execution_started"
    EXECUTION_SUCCEEDED = "execution_succeeded"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_BLOCKED = "execution_blocked"
    RETRY_SCHEDULED = "retry_scheduled"
    ROLLBACK_REQUESTED = "rollback_requested"
    ROLLBACK_COMPLETED = "rollback_completed"

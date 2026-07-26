from __future__ import annotations

from .enums import ExecutionStatus
from .errors import IllegalExecutionTransitionError


_ALLOWED: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.PENDING: {
        ExecutionStatus.READY,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.READY: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.ROLLBACK_PENDING,
    },
    ExecutionStatus.FAILED: {
        ExecutionStatus.READY,
        ExecutionStatus.ROLLBACK_PENDING,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.ROLLBACK_PENDING: {
        ExecutionStatus.ROLLED_BACK,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.SUCCEEDED: set(),
    ExecutionStatus.BLOCKED: {
        ExecutionStatus.READY,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.CANCELLED: set(),
    ExecutionStatus.ROLLED_BACK: set(),
}


def validate_transition(
    current: ExecutionStatus,
    target: ExecutionStatus,
) -> None:
    if target not in _ALLOWED[current]:
        raise IllegalExecutionTransitionError(
            f"Illegal execution transition: {current.value} -> {target.value}"
        )

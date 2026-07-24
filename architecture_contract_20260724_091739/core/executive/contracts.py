"""Protocols and exceptions for executive orchestration."""

from __future__ import annotations

from typing import Protocol

from core.executive.models import Mission, MissionTask, TaskExecutionResult


class DirectorHandler(Protocol):
    """Callable contract implemented by every task director."""

    def __call__(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> TaskExecutionResult:
        ...


class ExecutiveError(RuntimeError):
    """Base exception for the Gen 2 executive layer."""


class DirectorNotRegisteredError(ExecutiveError):
    """Raised when a task references an unknown director."""


class MissionNotFoundError(ExecutiveError):
    """Raised when a mission cannot be found."""


class InvalidMissionPlanError(ExecutiveError):
    """Raised when mission dependencies are invalid or cyclic."""

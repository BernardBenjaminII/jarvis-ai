"""Planning-engine exception hierarchy."""

from __future__ import annotations


class PlanningEngineError(RuntimeError):
    """Base exception for planning-engine failures."""


class InvalidExecutionSnapshotError(PlanningEngineError):
    """Raised when execution-state input is internally inconsistent."""


class PlanningGraphError(PlanningEngineError):
    """Raised when a mission plan cannot be represented safely."""


class DuplicateWorkItemError(PlanningGraphError):
    """Raised when multiple hierarchy elements use the same identifier."""


class UnknownWorkItemError(PlanningGraphError):
    """Raised when analysis references a work item that does not exist."""


class UnknownDependencyReferenceError(PlanningGraphError):
    """Raised when a dependency references an unknown work item."""


class PlanningCycleError(PlanningGraphError):
    """Raised when the analyzed execution graph contains a cycle."""


class UnsupportedPlanningPolicyError(PlanningEngineError):
    """Raised when a requested ranking policy is unsupported."""

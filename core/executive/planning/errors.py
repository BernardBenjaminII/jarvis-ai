"""Exceptions raised by the JARVIS planning data model."""

from __future__ import annotations


class PlanningError(Exception):
    """Base class for planning subsystem errors."""


class PlanningValidationError(PlanningError):
    """Raised when a plan violates one or more planning invariants."""

    def __init__(self, message: str, *, violations: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.violations = violations


class DependencyGraphError(PlanningValidationError):
    """Raised when a dependency graph is invalid."""


class DependencyCycleError(DependencyGraphError):
    """Raised when a dependency cycle is detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        self.cycle = cycle
        rendered = " -> ".join(cycle)
        super().__init__(
            f"Dependency cycle detected: {rendered}",
            violations=(f"dependency_cycle:{rendered}",),
        )


class MissingPlanElementError(DependencyGraphError):
    """Raised when a dependency references an unknown plan element."""


class DuplicatePlanElementError(PlanningValidationError):
    """Raised when two plan elements share the same identifier."""


class InvalidPlanTransitionError(PlanningError):
    """Raised when an invalid plan-state transition is requested."""


class PlanNotFoundError(PlanningError):
    """Raised when a requested plan cannot be found."""


class PlanVersionConflictError(PlanningError):
    """Raised when plan version history becomes inconsistent."""


class ImmutablePlanVersionError(PlanningError):
    """Raised when code attempts to overwrite an immutable plan version."""

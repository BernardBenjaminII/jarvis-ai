from __future__ import annotations


class ObservationEngineError(RuntimeError):
    """Base error for the Observation Engine."""


class ObservationValidationError(ObservationEngineError):
    """Raised when observation validation fails."""


class ObservationNotFoundError(ObservationEngineError):
    """Raised when an observation cannot be found."""


class DuplicateObservationError(ObservationEngineError):
    """Raised when duplicate registration is disallowed."""


class ObservationConflictError(ObservationEngineError):
    """Raised when an unresolved observation conflict blocks an operation."""


class InvalidLifecycleTransitionError(ObservationEngineError):
    """Raised when an observation lifecycle transition is invalid."""


__all__ = (
    "DuplicateObservationError",
    "InvalidLifecycleTransitionError",
    "ObservationConflictError",
    "ObservationEngineError",
    "ObservationNotFoundError",
    "ObservationValidationError",
)

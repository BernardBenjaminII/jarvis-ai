"""Domain errors for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations


class SituationError(Exception):
    """Base error for situation-model operations."""


class InvalidSituationError(SituationError, ValueError):
    """Raised when a situation violates the canonical contract."""


class SituationNotFoundError(SituationError, LookupError):
    """Raised when a requested situation does not exist."""


class SituationRepositoryClosedError(SituationError):
    """Raised when a closed situation repository is accessed."""


class ObservationCompatibilityError(SituationError, TypeError):
    """Raised when an input is not a Genesis IV-A1 observation."""

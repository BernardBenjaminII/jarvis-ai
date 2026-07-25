"""Domain errors for Genesis IV-A3 Executive Hypothesis Engine."""

from __future__ import annotations


class HypothesisError(Exception):
    """Base error for hypothesis operations."""


class InvalidHypothesisError(HypothesisError, ValueError):
    """Raised when a hypothesis violates the canonical contract."""


class HypothesisNotFoundError(HypothesisError, LookupError):
    """Raised when a requested hypothesis does not exist."""


class HypothesisRepositoryClosedError(HypothesisError):
    """Raised when a closed hypothesis repository is accessed."""


class SituationCompatibilityError(HypothesisError, TypeError):
    """Raised when an input is not a Genesis IV-A2 situation."""

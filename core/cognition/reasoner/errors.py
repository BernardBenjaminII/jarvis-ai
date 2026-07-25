"""Errors for Genesis IV-A5 Executive Reasoner."""

from __future__ import annotations


class ExecutiveReasoningError(Exception):
    """Base error for executive reasoning operations."""


class InvalidReasoningInputError(ExecutiveReasoningError, ValueError):
    """Raised when supplied reasoning inputs violate the contract."""


class InvalidReasoningResultError(ExecutiveReasoningError, ValueError):
    """Raised when a reasoning result violates the contract."""


class ReasoningResultNotFoundError(ExecutiveReasoningError, LookupError):
    """Raised when a requested reasoning result does not exist."""


class ReasoningRepositoryClosedError(ExecutiveReasoningError):
    """Raised when a closed reasoning repository is accessed."""

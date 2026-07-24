"""Errors for Genesis II-A3 constitutional reasoning context."""

from __future__ import annotations


class ReasoningContextError(Exception):
    """Base error for constitutional reasoning-context failures."""


class ReasoningContextContractError(ReasoningContextError, ValueError):
    """Raised when a reasoning-context contract is invalid."""


class DuplicateReasoningContextKeyError(ReasoningContextContractError):
    """Raised when a keyed context collection contains duplicate keys."""


__all__ = [
    "DuplicateReasoningContextKeyError",
    "ReasoningContextContractError",
    "ReasoningContextError",
]

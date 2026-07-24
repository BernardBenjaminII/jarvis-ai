"""Errors raised by the Genesis II reasoning-session lifecycle."""

from __future__ import annotations


class ReasoningSessionLifecycleError(ValueError):
    """Base error for reasoning-session lifecycle violations."""


class InvalidReasoningSessionTransitionError(ReasoningSessionLifecycleError):
    """Raised when a session requests an illegal lifecycle transition."""


class TerminalReasoningSessionError(
    InvalidReasoningSessionTransitionError
):
    """Raised when attempting to transition a terminal session."""


class ReasoningSessionContractError(ReasoningSessionLifecycleError):
    """Raised when an object does not satisfy the session contract."""

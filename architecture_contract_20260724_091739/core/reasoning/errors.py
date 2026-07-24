"""Errors raised by the JARVIS Reasoning Engine foundation."""

from __future__ import annotations


class ReasoningError(RuntimeError):
    """Base error for deterministic reasoning failures."""


class InvalidReasoningRequestError(ReasoningError):
    """Raised when a reasoning request violates its contracts."""


class UnknownEvidenceReferenceError(ReasoningError):
    """Raised when a hypothesis references evidence that does not exist."""


class DuplicateReasoningElementError(ReasoningError):
    """Raised when evidence or hypothesis identifiers are duplicated."""

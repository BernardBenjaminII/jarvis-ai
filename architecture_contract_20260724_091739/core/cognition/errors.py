"""Exceptions for the Genesis VI-A1 executive cognition foundation."""

from __future__ import annotations


class CognitionError(Exception):
    """Base exception for cognition-layer failures."""


class InvalidCognitiveContextError(CognitionError):
    """Raised when an executive context violates kernel invariants."""


class InvalidCognitiveStateError(CognitionError):
    """Raised when a cognitive state value is invalid."""


class InvalidStateTransitionError(CognitionError):
    """Raised when a requested cognitive-state transition is invalid."""


class WorkingMemoryCapacityError(CognitionError):
    """Raised when working memory cannot admit an item safely."""


class DuplicateMemoryEntryError(CognitionError):
    """Raised when a duplicate working-memory entry is admitted."""


class AttentionAllocationError(CognitionError):
    """Raised when an attention allocation is invalid."""


class CognitionCycleClosedError(CognitionError):
    """Raised when a closed cognition cycle is mutated."""


class CognitionCycleNotActiveError(CognitionError):
    """Raised when an operation requires an active cognition cycle."""

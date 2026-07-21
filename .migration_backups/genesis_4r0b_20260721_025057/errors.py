"""Domain exceptions for the Genesis IV cognition layer."""

from __future__ import annotations


class CognitionError(RuntimeError):
    """Base exception for cognition-domain failures."""


class CognitionValidationError(CognitionError, ValueError):
    """Raised when a cognition contract violates its invariants."""


class CognitionIdentifierError(CognitionValidationError):
    """Raised when a deterministic cognition identifier is invalid."""


class CognitionSerializationError(CognitionError):
    """Raised when a cognition object cannot be serialized canonically."""


class UnsupportedCognitiveObjectError(CognitionValidationError):
    """Raised when a validator receives an unsupported cognition object."""

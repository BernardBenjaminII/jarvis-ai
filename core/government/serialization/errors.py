"""Serialization-domain exceptions for Genesis VIII-A0-3."""

from __future__ import annotations


class GovernmentSerializationError(ValueError):
    """Base error for canonical Government serialization."""


class UnsupportedGovernmentSchemaError(GovernmentSerializationError):
    """Raised when an envelope declares an unsupported schema version."""


class GovernmentFingerprintError(GovernmentSerializationError):
    """Raised when serialized content fails integrity verification."""


class GovernmentPayloadError(GovernmentSerializationError):
    """Raised when an envelope contains an invalid or mismatched payload."""

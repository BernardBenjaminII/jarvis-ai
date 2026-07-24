"""Domain exceptions for the Genesis II-A4 Evidence model."""

from __future__ import annotations


class EvidenceError(Exception):
    """Base exception for canonical Evidence domain failures."""


class EvidenceValidationError(EvidenceError, ValueError):
    """Raised when an Evidence contract violates a constitutional invariant."""


class EvidenceIdentityError(EvidenceValidationError):
    """Raised when a canonical Evidence identifier is malformed or inconsistent."""


class EvidenceSerializationError(EvidenceError):
    """Raised when a value cannot be canonically serialized."""


class EvidenceUncertaintyError(EvidenceValidationError):
    """Raised when an uncertainty representation is structurally invalid."""


class EvidenceTemporalError(EvidenceValidationError):
    """Raised when Evidence temporal metadata is invalid."""


class EvidenceRelationshipError(EvidenceValidationError):
    """Raised when an Evidence relationship violates its contract."""

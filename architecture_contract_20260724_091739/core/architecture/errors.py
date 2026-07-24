"""Architecture Intelligence exception hierarchy."""

from __future__ import annotations


class ArchitectureError(Exception):
    """Base error for Architecture Intelligence."""


class ArchitectureValidationError(ArchitectureError):
    """Raised when an architecture contract violates an invariant."""


class ArchitectureSerializationError(ArchitectureError):
    """Raised when architecture data cannot be serialized canonically."""


class ArchitectureFingerprintError(ArchitectureError):
    """Raised when a deterministic fingerprint cannot be produced."""


class ArchitectureOwnershipError(ArchitectureError):
    """Raised for invalid or conflicting ownership declarations."""


class ArchitectureDependencyError(ArchitectureError):
    """Raised for invalid dependency declarations or policies."""


class ArchitectureCompatibilityError(ArchitectureError):
    """Raised when compatibility analysis cannot be completed safely."""


class ArchitectureMigrationError(ArchitectureError):
    """Raised for invalid migration plans or transitions."""


class ArchitectureCertificationError(ArchitectureError):
    """Raised when certification requirements are invalid or incomplete."""


__all__ = [
    "ArchitectureCertificationError",
    "ArchitectureCompatibilityError",
    "ArchitectureDependencyError",
    "ArchitectureError",
    "ArchitectureFingerprintError",
    "ArchitectureMigrationError",
    "ArchitectureOwnershipError",
    "ArchitectureSerializationError",
    "ArchitectureValidationError",
]

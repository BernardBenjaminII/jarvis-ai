"""Registry-domain exceptions for Genesis VIII-A0-4."""

from __future__ import annotations


class RegistryError(RuntimeError):
    """Base error for Organizational Registry contracts."""


class DuplicateObjectError(RegistryError):
    """Raised when an object already exists."""


class UnknownObjectError(RegistryError):
    """Raised when an object cannot be found."""


class DuplicateRelationshipError(RegistryError):
    """Raised when a relationship already exists."""


class UnknownRelationshipError(RegistryError):
    """Raised when a relationship cannot be found."""


class SnapshotError(RegistryError):
    """Raised when snapshot operations fail."""


class TransactionError(RegistryError):
    """Raised when registry transaction semantics are violated."""

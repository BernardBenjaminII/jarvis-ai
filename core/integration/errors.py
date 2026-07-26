"""Integration-plane exception hierarchy."""

from __future__ import annotations


class IntegrationError(Exception):
    """Base exception for the Executive Integration Plane."""


class InvalidIntegrationDefinitionError(IntegrationError, ValueError):
    """Raised when an integration contract is invalid."""


class DuplicateCapabilityError(IntegrationError):
    """Raised when an Integration capability identifier is duplicated."""


class UnknownCapabilityError(IntegrationError, LookupError):
    """Raised when an Integration capability identifier is unknown."""


class DuplicateProjectionProviderError(IntegrationError):
    """Raised when a projection provider identifier is duplicated."""


class ProjectionProviderNotFoundError(IntegrationError, LookupError):
    """Raised when a requested projection provider is not registered."""


class ProjectionExecutionError(IntegrationError):
    """Raised when strict projection execution cannot complete."""


__all__ = [
    "DuplicateCapabilityError",
    "DuplicateProjectionProviderError",
    "IntegrationError",
    "InvalidIntegrationDefinitionError",
    "ProjectionExecutionError",
    "ProjectionProviderNotFoundError",
    "UnknownCapabilityError",
]

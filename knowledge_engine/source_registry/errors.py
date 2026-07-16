"""Errors for JARVIS Phase VII-B2 source registry."""


class SourceRegistryError(RuntimeError):
    """Base source-registry error."""


class SourceNotAdmittedError(SourceRegistryError):
    """Raised when a rejected or review-required source is registered."""


class SourceRegistryConflictError(SourceRegistryError):
    """Raised when a source identity conflicts with an existing record."""


class SourceRegistryNotFoundError(SourceRegistryError):
    """Raised when a requested source does not exist."""


class InvalidLifecycleTransitionError(SourceRegistryError):
    """Raised when a lifecycle transition is not allowed."""

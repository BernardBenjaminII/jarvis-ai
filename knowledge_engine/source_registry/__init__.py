"""Public API for JARVIS Phase VII-B2 source registry."""

from .contracts import (
    RegisteredSource,
    RegistrationResult,
    RegistryStats,
    SourceLifecycleState,
)
from .errors import (
    InvalidLifecycleTransitionError,
    SourceNotAdmittedError,
    SourceRegistryConflictError,
    SourceRegistryError,
    SourceRegistryNotFoundError,
)
from .repository import SQLiteSourceRegistryRepository
from .service import SourceRegistryService

__all__ = [
    "InvalidLifecycleTransitionError",
    "RegisteredSource",
    "RegistrationResult",
    "RegistryStats",
    "SQLiteSourceRegistryRepository",
    "SourceLifecycleState",
    "SourceNotAdmittedError",
    "SourceRegistryConflictError",
    "SourceRegistryError",
    "SourceRegistryNotFoundError",
    "SourceRegistryService",
]

"""Organizational Registry public API."""

from .bootstrap import (
    DIRECTORATE_NAMES,
    GovernmentBootstrapResult,
    bootstrap_government,
)
from .events import RegistryEvent, RegistryEventKind
from .exceptions import (
    DuplicateObjectError,
    DuplicateRelationshipError,
    RegistryError,
    SnapshotError,
    TransactionError,
    UnknownObjectError,
    UnknownRelationshipError,
)
from .interfaces import GovernmentRegistry
from .memory import InMemoryGovernmentRegistry, MemoryRegistryTransaction
from .provider import RegistryProvider
from .provider_memory import InMemoryRegistryProvider
from .query import GovernmentQuery, GraphQuery, ObjectQuery, RelationshipQuery
from .repository import (
    GovernmentSnapshotRepository,
    ObjectRepository,
    RelationshipRepository,
)
from .snapshot import GovernmentSnapshot
from .transaction import RegistryTransaction

__all__ = [
    "DIRECTORATE_NAMES",
    "DuplicateObjectError",
    "DuplicateRelationshipError",
    "GovernmentBootstrapResult",
    "GovernmentQuery",
    "GovernmentRegistry",
    "GovernmentSnapshot",
    "GovernmentSnapshotRepository",
    "GraphQuery",
    "InMemoryGovernmentRegistry",
    "InMemoryRegistryProvider",
    "MemoryRegistryTransaction",
    "ObjectQuery",
    "ObjectRepository",
    "RegistryError",
    "RegistryEvent",
    "RegistryEventKind",
    "RegistryProvider",
    "RegistryTransaction",
    "RelationshipQuery",
    "RelationshipRepository",
    "SnapshotError",
    "TransactionError",
    "UnknownObjectError",
    "UnknownRelationshipError",
    "bootstrap_government",
]

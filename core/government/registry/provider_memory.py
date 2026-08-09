"""In-memory registry provider for Genesis VIII-B0."""

from __future__ import annotations

from .interfaces import GovernmentRegistry
from .memory import InMemoryGovernmentRegistry
from .provider import RegistryProvider
from .repository import (
    GovernmentSnapshotRepository,
    ObjectRepository,
    RelationshipRepository,
)
from .transaction import RegistryTransaction


class InMemoryRegistryProvider(RegistryProvider):
    """Reference provider for the operational in-memory registry."""

    def __init__(self) -> None:
        self._registry = InMemoryGovernmentRegistry()

    def create_registry(self) -> GovernmentRegistry:
        return self._registry

    def create_object_repository(self) -> ObjectRepository:
        raise NotImplementedError(
            "VIII-B0 exposes the registry boundary; repository adapters follow later."
        )

    def create_relationship_repository(self) -> RelationshipRepository:
        raise NotImplementedError(
            "VIII-B0 exposes the registry boundary; repository adapters follow later."
        )

    def create_snapshot_repository(self) -> GovernmentSnapshotRepository:
        raise NotImplementedError(
            "VIII-B0 exposes the registry boundary; snapshot persistence follows later."
        )

    def create_transaction(self) -> RegistryTransaction:
        return self._registry.transaction()

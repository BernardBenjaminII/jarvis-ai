"""Abstract provider factory for Organizational Registry composition."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .interfaces import GovernmentRegistry
from .repository import (
    GovernmentSnapshotRepository,
    ObjectRepository,
    RelationshipRepository,
)
from .transaction import RegistryTransaction


class RegistryProvider(ABC):
    @abstractmethod
    def create_object_repository(self) -> ObjectRepository:
        raise NotImplementedError

    @abstractmethod
    def create_relationship_repository(self) -> RelationshipRepository:
        raise NotImplementedError

    @abstractmethod
    def create_snapshot_repository(self) -> GovernmentSnapshotRepository:
        raise NotImplementedError

    @abstractmethod
    def create_transaction(self) -> RegistryTransaction:
        raise NotImplementedError

    @abstractmethod
    def create_registry(self) -> GovernmentRegistry:
        raise NotImplementedError

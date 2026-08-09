"""Top-level Organizational Registry interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.government.models import ConstitutionalIdentifier, ConstitutionalObject
from core.government.relationships import (
    OrganizationalGraph,
    OrganizationalRelationship,
    RelationshipIdentifier,
)

from .events import RegistryEvent
from .query import GovernmentQuery, GraphQuery
from .snapshot import GovernmentSnapshot
from .transaction import RegistryTransaction


class GovernmentRegistry(ABC):
    @abstractmethod
    def register_object(self, value: ConstitutionalObject) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def update_object(self, value: ConstitutionalObject) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def remove_object(self, identifier: ConstitutionalIdentifier) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def get_object(self, identifier: ConstitutionalIdentifier) -> ConstitutionalObject:
        raise NotImplementedError

    @abstractmethod
    def register_relationship(
        self,
        value: OrganizationalRelationship,
    ) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def remove_relationship(
        self,
        identifier: RelationshipIdentifier,
    ) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def query(self, query: GovernmentQuery) -> GovernmentSnapshot:
        raise NotImplementedError

    @abstractmethod
    def graph(self, query: GraphQuery | None = None) -> OrganizationalGraph:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self, snapshot_id: str) -> GovernmentSnapshot:
        raise NotImplementedError

    @abstractmethod
    def restore(self, snapshot: GovernmentSnapshot) -> RegistryEvent:
        raise NotImplementedError

    @abstractmethod
    def transaction(self) -> RegistryTransaction:
        raise NotImplementedError

    @abstractmethod
    def fingerprint(self) -> str:
        raise NotImplementedError

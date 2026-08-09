"""Abstract repository contracts for Organizational Registry implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.government.models import ConstitutionalIdentifier, ConstitutionalObject
from core.government.relationships import (
    OrganizationalRelationship,
    RelationshipIdentifier,
)

from .query import ObjectQuery, RelationshipQuery
from .snapshot import GovernmentSnapshot


class ObjectRepository(ABC):
    @abstractmethod
    def store(self, value: ConstitutionalObject) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, value: ConstitutionalObject) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, identifier: ConstitutionalIdentifier) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, identifier: ConstitutionalIdentifier) -> ConstitutionalObject:
        raise NotImplementedError

    @abstractmethod
    def exists(self, identifier: ConstitutionalIdentifier) -> bool:
        raise NotImplementedError

    @abstractmethod
    def query(self, query: ObjectQuery) -> tuple[ConstitutionalObject, ...]:
        raise NotImplementedError

    @abstractmethod
    def count(self, query: ObjectQuery | None = None) -> int:
        raise NotImplementedError


class RelationshipRepository(ABC):
    @abstractmethod
    def store(self, value: OrganizationalRelationship) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, identifier: RelationshipIdentifier) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, identifier: RelationshipIdentifier) -> OrganizationalRelationship:
        raise NotImplementedError

    @abstractmethod
    def exists(self, identifier: RelationshipIdentifier) -> bool:
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        query: RelationshipQuery,
    ) -> tuple[OrganizationalRelationship, ...]:
        raise NotImplementedError

    @abstractmethod
    def count(self, query: RelationshipQuery | None = None) -> int:
        raise NotImplementedError


class GovernmentSnapshotRepository(ABC):
    @abstractmethod
    def store(self, snapshot: GovernmentSnapshot) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, snapshot_id: str) -> GovernmentSnapshot:
        raise NotImplementedError

    @abstractmethod
    def latest(self) -> GovernmentSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def list_snapshots(self) -> tuple[GovernmentSnapshot, ...]:
        raise NotImplementedError

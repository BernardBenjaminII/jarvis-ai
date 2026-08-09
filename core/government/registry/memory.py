"""In-memory Organizational Registry implementation for Genesis VIII-B0."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from typing import Iterable

from core.government.models import (
    ConstitutionalIdentifier,
    ConstitutionalObject,
    ConstitutionalObjectKind,
    LifecycleState,
)
from core.government.relationships import (
    OrganizationalGraph,
    OrganizationalRelationship,
    RelationshipIdentifier,
)
from core.government.serialization import GovernmentCodec

from .events import RegistryEvent, RegistryEventKind
from .exceptions import (
    DuplicateObjectError,
    DuplicateRelationshipError,
    SnapshotError,
    TransactionError,
    UnknownObjectError,
    UnknownRelationshipError,
)
from .interfaces import GovernmentRegistry
from .query import GovernmentQuery, GraphQuery, ObjectQuery, RelationshipQuery
from .snapshot import GovernmentSnapshot
from .transaction import RegistryTransaction


class MemoryRegistryTransaction(RegistryTransaction):
    """Copy-on-write transaction for the in-memory registry."""

    def __init__(self, registry: "InMemoryGovernmentRegistry") -> None:
        self._registry = registry
        self._active = False
        self._objects: dict[ConstitutionalIdentifier, ConstitutionalObject] = {}
        self._relationships: dict[RelationshipIdentifier, OrganizationalRelationship] = {}
        self._snapshots: dict[str, GovernmentSnapshot] = {}

    def begin(self) -> None:
        if self._active:
            raise TransactionError("transaction is already active")
        self._objects = dict(self._registry._objects)
        self._relationships = dict(self._registry._relationships)
        self._snapshots = dict(self._registry._snapshots)
        self._active = True

    def commit(self) -> None:
        if not self._active:
            raise TransactionError("transaction is not active")
        self._active = False

    def rollback(self) -> None:
        if not self._active:
            raise TransactionError("transaction is not active")
        self._registry._objects = self._objects
        self._registry._relationships = self._relationships
        self._registry._snapshots = self._snapshots
        self._active = False


class InMemoryGovernmentRegistry(GovernmentRegistry):
    """Deterministic, storage-independent reference implementation."""

    def __init__(self) -> None:
        self._objects: dict[ConstitutionalIdentifier, ConstitutionalObject] = {}
        self._relationships: dict[RelationshipIdentifier, OrganizationalRelationship] = {}
        self._snapshots: dict[str, GovernmentSnapshot] = {}

    def register_object(self, value: ConstitutionalObject) -> RegistryEvent:
        if value.identifier in self._objects:
            raise DuplicateObjectError(value.identifier.value)
        self._objects[value.identifier] = value
        return RegistryEvent(
            RegistryEventKind.OBJECT_REGISTERED,
            object_identifier=value.identifier,
        )

    def update_object(self, value: ConstitutionalObject) -> RegistryEvent:
        if value.identifier not in self._objects:
            raise UnknownObjectError(value.identifier.value)
        self._objects[value.identifier] = value
        return RegistryEvent(
            RegistryEventKind.OBJECT_UPDATED,
            object_identifier=value.identifier,
        )

    def remove_object(self, identifier: ConstitutionalIdentifier) -> RegistryEvent:
        if identifier not in self._objects:
            raise UnknownObjectError(identifier.value)
        for relationship in self._relationships.values():
            if relationship.source == identifier or relationship.target == identifier:
                raise TransactionError(
                    "object has registered relationships and cannot be removed"
                )
        del self._objects[identifier]
        return RegistryEvent(
            RegistryEventKind.OBJECT_REMOVED,
            object_identifier=identifier,
        )

    def get_object(self, identifier: ConstitutionalIdentifier) -> ConstitutionalObject:
        try:
            return self._objects[identifier]
        except KeyError as exc:
            raise UnknownObjectError(identifier.value) from exc

    def register_relationship(
        self,
        value: OrganizationalRelationship,
    ) -> RegistryEvent:
        if value.identifier in self._relationships:
            raise DuplicateRelationshipError(value.identifier.value)
        if value.source not in self._objects:
            raise UnknownObjectError(value.source.value)
        if value.target not in self._objects:
            raise UnknownObjectError(value.target.value)

        candidate = tuple(self._relationships.values()) + (value,)
        OrganizationalGraph.create(candidate)
        self._relationships[value.identifier] = value

        return RegistryEvent(
            RegistryEventKind.RELATIONSHIP_REGISTERED,
            relationship_identifier=value.identifier,
        )

    def remove_relationship(
        self,
        identifier: RelationshipIdentifier,
    ) -> RegistryEvent:
        if identifier not in self._relationships:
            raise UnknownRelationshipError(identifier.value)
        del self._relationships[identifier]
        return RegistryEvent(
            RegistryEventKind.RELATIONSHIP_REMOVED,
            relationship_identifier=identifier,
        )

    def query(self, query: GovernmentQuery) -> GovernmentSnapshot:
        objects = self._query_objects(query.objects)
        selected_ids = {item.identifier for item in objects}
        relationships = tuple(
            relationship
            for relationship in self._query_relationships(query.relationships)
            if relationship.source in selected_ids and relationship.target in selected_ids
        )
        snapshot_id = "query-" + sha256(
            json.dumps(
                {
                    "objects": [item.identifier.value for item in objects],
                    "relationships": [
                        item.identifier.value for item in relationships
                    ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:24]
        return GovernmentSnapshot(
            snapshot_id=snapshot_id,
            objects=objects,
            relationships=relationships,
        )

    def graph(self, query: GraphQuery | None = None) -> OrganizationalGraph:
        graph = OrganizationalGraph.create(self._relationships.values())
        if query is None or not query.roots:
            return graph

        allowed_kinds = set(query.relationship_kinds)
        max_depth = query.max_depth
        visited = set(query.roots)
        frontier = set(query.roots)
        selected: list[OrganizationalRelationship] = []
        depth = 0

        while frontier and (max_depth is None or depth < max_depth):
            next_frontier: set[ConstitutionalIdentifier] = set()
            for relationship in graph.relationships:
                if allowed_kinds and relationship.kind not in allowed_kinds:
                    continue
                if relationship.source in frontier:
                    selected.append(relationship)
                    if relationship.target not in visited:
                        next_frontier.add(relationship.target)
                elif relationship.target in frontier:
                    selected.append(relationship)
                    if relationship.source not in visited:
                        next_frontier.add(relationship.source)
            visited.update(next_frontier)
            frontier = next_frontier
            depth += 1

        return OrganizationalGraph.create(selected)

    def snapshot(self, snapshot_id: str) -> GovernmentSnapshot:
        if not snapshot_id.strip():
            raise SnapshotError("snapshot_id is required")
        snapshot = GovernmentSnapshot(
            snapshot_id=snapshot_id,
            objects=tuple(self._objects.values()),
            relationships=tuple(self._relationships.values()),
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    def restore(self, snapshot: GovernmentSnapshot) -> RegistryEvent:
        self._objects = {
            item.identifier: item
            for item in snapshot.objects
        }
        self._relationships = {
            item.identifier: item
            for item in snapshot.relationships
        }
        self._snapshots[snapshot.snapshot_id] = snapshot
        return RegistryEvent(
            RegistryEventKind.SNAPSHOT_RESTORED,
            snapshot_id=snapshot.snapshot_id,
        )

    def transaction(self) -> RegistryTransaction:
        return MemoryRegistryTransaction(self)

    def fingerprint(self) -> str:
        snapshot = GovernmentSnapshot(
            snapshot_id="registry-current",
            objects=tuple(self._objects.values()),
            relationships=tuple(self._relationships.values()),
        )
        return snapshot.fingerprint

    def _query_objects(
        self,
        query: ObjectQuery,
    ) -> tuple[ConstitutionalObject, ...]:
        values = list(self._objects.values())

        if query.kinds:
            allowed = set(query.kinds)
            values = [item for item in values if item.KIND in allowed]
        if query.lifecycle:
            allowed_lifecycle = set(query.lifecycle)
            values = [
                item for item in values
                if item.lifecycle in allowed_lifecycle
            ]
        if query.owner is not None:
            values = [item for item in values if item.owner == query.owner]
        if query.tags:
            required_tags = set(query.tags)
            values = [
                item for item in values
                if required_tags.issubset(set(item.tags))
            ]

        values.sort(key=lambda item: item.identifier.value)
        if query.limit is not None:
            values = values[: query.limit]
        return tuple(values)

    def _query_relationships(
        self,
        query: RelationshipQuery,
    ) -> tuple[OrganizationalRelationship, ...]:
        values = list(self._relationships.values())

        if query.kinds:
            allowed = set(query.kinds)
            values = [item for item in values if item.kind in allowed]
        if query.status:
            allowed_status = set(query.status)
            values = [item for item in values if item.status in allowed_status]
        if query.source is not None:
            values = [item for item in values if item.source == query.source]
        if query.target is not None:
            values = [item for item in values if item.target == query.target]

        values.sort(
            key=lambda item: (
                item.source.value,
                item.kind.value,
                item.target.value,
            )
        )
        if query.limit is not None:
            values = values[: query.limit]
        return tuple(values)

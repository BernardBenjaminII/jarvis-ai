"""Immutable query contracts for Organizational Registry access."""

from __future__ import annotations

from dataclasses import dataclass

from core.government.models import (
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    LifecycleState,
)
from core.government.relationships import RelationshipKind, RelationshipStatus


@dataclass(frozen=True, slots=True)
class ObjectQuery:
    kinds: tuple[ConstitutionalObjectKind, ...] = ()
    lifecycle: tuple[LifecycleState, ...] = ()
    owner: ConstitutionalIdentifier | None = None
    tags: tuple[str, ...] = ()
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be positive")
        object.__setattr__(self, "kinds", tuple(sorted(set(self.kinds), key=lambda item: item.value)))
        object.__setattr__(
            self,
            "lifecycle",
            tuple(sorted(set(self.lifecycle), key=lambda item: item.value)),
        )
        object.__setattr__(
            self,
            "tags",
            tuple(sorted({tag.strip().lower() for tag in self.tags if tag.strip()})),
        )


@dataclass(frozen=True, slots=True)
class RelationshipQuery:
    kinds: tuple[RelationshipKind, ...] = ()
    status: tuple[RelationshipStatus, ...] = ()
    source: ConstitutionalIdentifier | None = None
    target: ConstitutionalIdentifier | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be positive")
        object.__setattr__(
            self,
            "kinds",
            tuple(sorted(set(self.kinds), key=lambda item: item.value)),
        )
        object.__setattr__(
            self,
            "status",
            tuple(sorted(set(self.status), key=lambda item: item.value)),
        )


@dataclass(frozen=True, slots=True)
class GovernmentQuery:
    objects: ObjectQuery = ObjectQuery()
    relationships: RelationshipQuery = RelationshipQuery()


@dataclass(frozen=True, slots=True)
class GraphQuery:
    roots: tuple[ConstitutionalIdentifier, ...] = ()
    relationship_kinds: tuple[RelationshipKind, ...] = ()
    max_depth: int | None = None

    def __post_init__(self) -> None:
        if self.max_depth is not None and self.max_depth < 0:
            raise ValueError("max_depth cannot be negative")
        object.__setattr__(
            self,
            "roots",
            tuple(sorted(set(self.roots), key=lambda item: item.value)),
        )
        object.__setattr__(
            self,
            "relationship_kinds",
            tuple(sorted(set(self.relationship_kinds), key=lambda item: item.value)),
        )

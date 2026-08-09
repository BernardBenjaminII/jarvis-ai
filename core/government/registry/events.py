"""Descriptive Organizational Registry events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.government.models import ConstitutionalIdentifier
from core.government.relationships import RelationshipIdentifier


class RegistryEventKind(str, Enum):
    OBJECT_REGISTERED = "object_registered"
    OBJECT_UPDATED = "object_updated"
    OBJECT_REMOVED = "object_removed"
    RELATIONSHIP_REGISTERED = "relationship_registered"
    RELATIONSHIP_REMOVED = "relationship_removed"
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_RESTORED = "snapshot_restored"


@dataclass(frozen=True, slots=True)
class RegistryEvent:
    kind: RegistryEventKind
    object_identifier: ConstitutionalIdentifier | None = None
    relationship_identifier: RelationshipIdentifier | None = None
    snapshot_id: str | None = None

    def __post_init__(self) -> None:
        populated = sum(
            value is not None
            for value in (
                self.object_identifier,
                self.relationship_identifier,
                self.snapshot_id,
            )
        )
        if populated != 1:
            raise ValueError("registry event must identify exactly one subject")

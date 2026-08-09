"""Immutable Government snapshot contracts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from core.government.models import ConstitutionalObject
from core.government.relationships import OrganizationalGraph, OrganizationalRelationship
from core.government.serialization import GOVERNMENT_SCHEMA_VERSION, GovernmentCodec


@dataclass(frozen=True, slots=True)
class GovernmentSnapshot:
    snapshot_id: str
    objects: tuple[ConstitutionalObject, ...]
    relationships: tuple[OrganizationalRelationship, ...]
    schema_version: str = GOVERNMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        object.__setattr__(self, "snapshot_id", self.snapshot_id.strip())
        object.__setattr__(
            self,
            "objects",
            tuple(sorted(self.objects, key=lambda item: item.identifier.value)),
        )
        graph = OrganizationalGraph.create(self.relationships)
        object.__setattr__(self, "relationships", graph.relationships)

    @property
    def graph(self) -> OrganizationalGraph:
        return OrganizationalGraph.create(self.relationships)

    @property
    def fingerprint(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "schema_version": self.schema_version,
            "objects": [GovernmentCodec.encode(item).to_dict() for item in self.objects],
            "relationships": [
                GovernmentCodec.encode(item).to_dict()
                for item in self.relationships
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

"""Canonical codec for Government objects, relationships, and graphs."""

from __future__ import annotations

from typing import Union

from core.government.models import ConstitutionalObject, object_from_dict
from core.government.relationships import (
    OrganizationalGraph,
    OrganizationalRelationship,
    relationship_from_dict,
)

from .envelope import GovernmentEnvelope
from .errors import GovernmentPayloadError


GovernmentSerializable = Union[
    ConstitutionalObject,
    OrganizationalRelationship,
    OrganizationalGraph,
]


class GovernmentCodec:
    """Encode and reconstruct certified Government Framework values."""

    @staticmethod
    def encode(
        value: GovernmentSerializable,
        *,
        metadata: dict[str, str] | None = None,
    ) -> GovernmentEnvelope:
        if isinstance(value, ConstitutionalObject):
            payload_type = "constitutional_object"
            payload = value.to_dict()
        elif isinstance(value, OrganizationalRelationship):
            payload_type = "organizational_relationship"
            payload = value.to_dict()
        elif isinstance(value, OrganizationalGraph):
            payload_type = "organizational_graph"
            payload = {
                "relationships": [
                    relationship.to_dict()
                    for relationship in value.relationships
                ],
                "graph_fingerprint": value.fingerprint,
            }
        else:
            raise GovernmentPayloadError(
                f"unsupported Government value: {type(value).__name__}"
            )

        return GovernmentEnvelope(
            payload_type=payload_type,
            payload=payload,
            metadata=metadata or {},
        )

    @staticmethod
    def decode(
        envelope: GovernmentEnvelope,
    ) -> GovernmentSerializable:
        if envelope.payload_type == "constitutional_object":
            return object_from_dict(envelope.payload)

        if envelope.payload_type == "organizational_relationship":
            return relationship_from_dict(envelope.payload)

        if envelope.payload_type == "organizational_graph":
            raw_relationships = envelope.payload.get("relationships")
            if not isinstance(raw_relationships, list):
                raise GovernmentPayloadError(
                    "organizational graph relationships must be a list"
                )

            graph = OrganizationalGraph.create(
                relationship_from_dict(item)
                for item in raw_relationships
            )
            supplied = envelope.payload.get("graph_fingerprint")
            if supplied and supplied != graph.fingerprint:
                raise GovernmentPayloadError(
                    "organizational graph fingerprint is invalid"
                )
            return graph

        raise GovernmentPayloadError(
            f"unsupported Government payload type: {envelope.payload_type}"
        )

    @classmethod
    def dumps(
        cls,
        value: GovernmentSerializable,
        *,
        metadata: dict[str, str] | None = None,
    ) -> str:
        return cls.encode(value, metadata=metadata).to_json()

    @classmethod
    def loads(cls, serialized: str) -> GovernmentSerializable:
        return cls.decode(GovernmentEnvelope.from_json(serialized))

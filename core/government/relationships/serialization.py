from typing import Any, Mapping
from core.government.models import ConstitutionalIdentifier
from .enums import RelationshipKind, RelationshipStatus
from .models import OrganizationalRelationship

def relationship_from_dict(payload: Mapping[str, Any]) -> OrganizationalRelationship:
    relationship = OrganizationalRelationship(
        source=ConstitutionalIdentifier.parse(str(payload["source"])),
        kind=RelationshipKind(str(payload["kind"])),
        target=ConstitutionalIdentifier.parse(str(payload["target"])),
        status=RelationshipStatus(str(payload["status"])),
        constitutional_basis=tuple(payload.get("constitutional_basis", ())),
        metadata=dict(payload.get("metadata", {})),
    )
    supplied = payload.get("identifier")
    if supplied and supplied != relationship.identifier.value:
        raise ValueError("serialized relationship identifier is invalid")
    return relationship

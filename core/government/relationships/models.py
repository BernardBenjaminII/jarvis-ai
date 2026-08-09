from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping
from core.government.models import ConstitutionalIdentifier
from .enums import RelationshipKind, RelationshipStatus
from .identifiers import RelationshipIdentifier

_HIERARCHICAL_KINDS = frozenset({
    RelationshipKind.OWNS,
    RelationshipKind.COMMANDS,
    RelationshipKind.REPORTS_TO,
    RelationshipKind.MEMBER_OF,
    RelationshipKind.GOVERNS,
})

@dataclass(frozen=True, slots=True)
class OrganizationalRelationship:
    source: ConstitutionalIdentifier
    kind: RelationshipKind
    target: ConstitutionalIdentifier
    status: RelationshipStatus = RelationshipStatus.PROPOSED
    constitutional_basis: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("a relationship cannot target its own source")
        object.__setattr__(
            self, "constitutional_basis",
            tuple(sorted({x.strip() for x in self.constitutional_basis if x.strip()}))
        )
        object.__setattr__(
            self, "metadata",
            dict(sorted((str(k), str(v)) for k, v in self.metadata.items()))
        )

    @property
    def identifier(self) -> RelationshipIdentifier:
        return RelationshipIdentifier(self.source, self.kind, self.target)

    @property
    def is_hierarchical(self) -> bool:
        return self.kind in _HIERARCHICAL_KINDS

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier.value,
            "source": self.source.value,
            "kind": self.kind.value,
            "target": self.target.value,
            "status": self.status.value,
            "constitutional_basis": list(self.constitutional_basis),
            "metadata": dict(self.metadata),
        }

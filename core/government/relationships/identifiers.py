from dataclasses import dataclass
from hashlib import sha256
from core.government.models import ConstitutionalIdentifier
from .enums import RelationshipKind

@dataclass(frozen=True, slots=True, order=True)
class RelationshipIdentifier:
    source: ConstitutionalIdentifier
    kind: RelationshipKind
    target: ConstitutionalIdentifier

    @property
    def value(self) -> str:
        material = f"{self.source.value}|{self.kind.value}|{self.target.value}"
        digest = sha256(material.encode("utf-8")).hexdigest()[:24]
        return f"relationship:{self.kind.value}:{digest}"

    def __str__(self) -> str:
        return self.value

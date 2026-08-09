from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable
from core.government.models import ConstitutionalIdentifier
from .enums import RelationshipKind
from .models import OrganizationalRelationship

class OrganizationalGraphError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class OrganizationalGraph:
    relationships: tuple[OrganizationalRelationship, ...]

    @classmethod
    def create(cls, relationships: Iterable[OrganizationalRelationship]) -> "OrganizationalGraph":
        normalized = tuple(sorted(
            relationships,
            key=lambda r: (r.source.value, r.kind.value, r.target.value),
        ))
        ids = tuple(r.identifier.value for r in normalized)
        if len(ids) != len(set(ids)):
            raise OrganizationalGraphError("duplicate organizational relationship")
        graph = cls(normalized)
        graph._validate_single_parent(RelationshipKind.OWNS)
        graph._validate_single_parent(RelationshipKind.REPORTS_TO)
        graph._validate_single_parent(RelationshipKind.MEMBER_OF)
        graph._validate_acyclic_hierarchies()
        return graph

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(
            [r.to_dict() for r in self.relationships],
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()

    def outgoing(self, source: ConstitutionalIdentifier, *, kind: RelationshipKind | None = None):
        return tuple(
            r for r in self.relationships
            if r.source == source and (kind is None or r.kind is kind)
        )

    def incoming(self, target: ConstitutionalIdentifier, *, kind: RelationshipKind | None = None):
        return tuple(
            r for r in self.relationships
            if r.target == target and (kind is None or r.kind is kind)
        )

    def dependencies_of(self, source: ConstitutionalIdentifier):
        return tuple(
            r.target for r in self.outgoing(source, kind=RelationshipKind.DEPENDS_ON)
        )

    def _validate_single_parent(self, kind: RelationshipKind) -> None:
        parents = {}
        for r in self.relationships:
            if r.kind is not kind:
                continue
            child = r.target if kind is RelationshipKind.OWNS else r.source
            parent = r.source if kind is RelationshipKind.OWNS else r.target
            prior = parents.get(child)
            if prior is not None and prior != parent:
                raise OrganizationalGraphError(
                    f"{child.value} has multiple {kind.value} parents"
                )
            parents[child] = parent

    def _validate_acyclic_hierarchies(self) -> None:
        kinds = (
            RelationshipKind.OWNS,
            RelationshipKind.COMMANDS,
            RelationshipKind.REPORTS_TO,
            RelationshipKind.MEMBER_OF,
            RelationshipKind.GOVERNS,
        )
        for kind in kinds:
            adjacency = {}
            for r in self.relationships:
                if r.kind is kind:
                    adjacency.setdefault(r.source, set()).add(r.target)
            visiting, visited = set(), set()

            def visit(node):
                if node in visiting:
                    raise OrganizationalGraphError(
                        f"cycle detected in {kind.value} relationships"
                    )
                if node in visited:
                    return
                visiting.add(node)
                for target in adjacency.get(node, set()):
                    visit(target)
                visiting.remove(node)
                visited.add(node)

            for node in tuple(adjacency):
                visit(node)

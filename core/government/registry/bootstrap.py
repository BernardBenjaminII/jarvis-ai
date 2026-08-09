"""Canonical Government bootstrap definitions."""

from __future__ import annotations

from dataclasses import dataclass

from core.government.models import (
    AuthorityLevel,
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    Directorate,
    ExecutiveOffice,
    Government,
    LifecycleState,
)
from core.government.relationships import OrganizationalRelationship, RelationshipKind

from .memory import InMemoryGovernmentRegistry
from .query import GovernmentQuery


DIRECTORATE_NAMES = (
    "executive",
    "knowledge",
    "reasoning",
    "planning",
    "engineering",
    "operations",
    "observation",
    "security",
    "mission-control",
    "acquisition",
    "communications",
    "runtime",
    "robotics",
)


@dataclass(frozen=True, slots=True)
class GovernmentBootstrapResult:
    registry: InMemoryGovernmentRegistry
    object_count: int
    relationship_count: int
    fingerprint: str


def bootstrap_government() -> GovernmentBootstrapResult:
    registry = InMemoryGovernmentRegistry()

    government_id = ConstitutionalIdentifier(
        ConstitutionalObjectKind.GOVERNMENT,
        "jarvis",
        "government",
    )
    executive_id = ConstitutionalIdentifier(
        ConstitutionalObjectKind.EXECUTIVE,
        "government",
        "executive",
    )

    registry.register_object(
        Government(
            identifier=government_id,
            title="JARVIS Government",
            mission="Coordinate the Executive Operating System.",
            authority=AuthorityLevel.CONSTITUTIONAL,
            lifecycle=LifecycleState.ACTIVE,
            constitutional_basis=("GOA-0000",),
        )
    )
    registry.register_object(
        ExecutiveOffice(
            identifier=executive_id,
            title="Office of the Executive",
            mission="Coordinate the Government.",
            authority=AuthorityLevel.EXECUTIVE,
            lifecycle=LifecycleState.ACTIVE,
            owner=government_id,
            constitutional_basis=("GOA-0000 Part IV",),
        )
    )
    registry.register_relationship(
        OrganizationalRelationship(
            government_id,
            RelationshipKind.OWNS,
            executive_id,
            constitutional_basis=("GOA-0000 Article XIV",),
        )
    )

    for name in DIRECTORATE_NAMES:
        directorate_id = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DIRECTORATE,
            "government",
            name,
        )
        registry.register_object(
            Directorate(
                identifier=directorate_id,
                title=f"{name.replace('-', ' ').title()} Directorate",
                mission=f"Execute the enduring {name.replace('-', ' ')} function.",
                authority=AuthorityLevel.DIRECTORATE,
                lifecycle=LifecycleState.ACTIVE,
                owner=executive_id,
                constitutional_basis=("GOA-0000 Part V",),
            )
        )
        registry.register_relationship(
            OrganizationalRelationship(
                executive_id,
                RelationshipKind.COMMANDS,
                directorate_id,
                constitutional_basis=("GOA-0000 Article XIV",),
            )
        )

    return GovernmentBootstrapResult(
        registry=registry,
        object_count=len(registry.query(GovernmentQuery()).objects),
        relationship_count=len(registry.graph().relationships),
        fingerprint=registry.fingerprint(),
    )

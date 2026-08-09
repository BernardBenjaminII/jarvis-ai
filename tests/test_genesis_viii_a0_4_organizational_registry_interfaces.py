from __future__ import annotations

from abc import ABC
import inspect
import unittest

from core.government import (
    AuthorityLevel,
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    Department,
    Directorate,
    GovernmentQuery,
    GovernmentRegistry,
    GovernmentSnapshot,
    GraphQuery,
    LifecycleState,
    ObjectQuery,
    ObjectRepository,
    OrganizationalRelationship,
    RegistryEvent,
    RegistryEventKind,
    RegistryProvider,
    RegistryTransaction,
    RelationshipKind,
    RelationshipQuery,
    RelationshipRepository,
)


class OrganizationalRegistryInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.knowledge = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DIRECTORATE,
            "government",
            "knowledge",
        )
        self.assimilation = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DEPARTMENT,
            "knowledge",
            "assimilation",
        )
        self.directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward organizational knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
            lifecycle=LifecycleState.ACTIVE,
        )
        self.department = Department(
            identifier=self.assimilation,
            title="Assimilation Department",
            mission="Transform admitted sources into governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            owner=self.knowledge,
            lifecycle=LifecycleState.ACTIVE,
        )
        self.relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )

    def test_interfaces_are_abstract(self) -> None:
        for contract in (
            GovernmentRegistry,
            ObjectRepository,
            RelationshipRepository,
            RegistryProvider,
            RegistryTransaction,
        ):
            self.assertTrue(inspect.isabstract(contract), contract.__name__)

    def test_query_contracts_are_immutable_and_normalized(self) -> None:
        query = ObjectQuery(
            kinds=(
                ConstitutionalObjectKind.DEPARTMENT,
                ConstitutionalObjectKind.DEPARTMENT,
            ),
            tags=("Knowledge", "knowledge", " Assimilation "),
            limit=10,
        )
        self.assertEqual(query.kinds, (ConstitutionalObjectKind.DEPARTMENT,))
        self.assertEqual(query.tags, ("assimilation", "knowledge"))
        with self.assertRaises(AttributeError):
            query.limit = 2

    def test_relationship_query_is_deterministic(self) -> None:
        first = RelationshipQuery(
            kinds=(RelationshipKind.OWNS, RelationshipKind.DEPENDS_ON),
        )
        second = RelationshipQuery(
            kinds=(RelationshipKind.DEPENDS_ON, RelationshipKind.OWNS),
        )
        self.assertEqual(first, second)

    def test_graph_query_rejects_negative_depth(self) -> None:
        with self.assertRaises(ValueError):
            GraphQuery(max_depth=-1)

    def test_snapshot_is_deterministic(self) -> None:
        first = GovernmentSnapshot(
            snapshot_id="snapshot-1",
            objects=(self.department, self.directorate),
            relationships=(self.relationship,),
        )
        second = GovernmentSnapshot(
            snapshot_id="snapshot-1",
            objects=(self.directorate, self.department),
            relationships=(self.relationship,),
        )
        self.assertEqual(first, second)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_snapshot_graph_is_validated(self) -> None:
        snapshot = GovernmentSnapshot(
            snapshot_id="snapshot-2",
            objects=(self.directorate, self.department),
            relationships=(self.relationship,),
        )
        self.assertEqual(snapshot.graph.relationships, (self.relationship,))

    def test_registry_event_has_exactly_one_subject(self) -> None:
        event = RegistryEvent(
            RegistryEventKind.OBJECT_REGISTERED,
            object_identifier=self.assimilation,
        )
        self.assertEqual(event.object_identifier, self.assimilation)

        with self.assertRaises(ValueError):
            RegistryEvent(
                RegistryEventKind.OBJECT_REGISTERED,
                object_identifier=self.assimilation,
                snapshot_id="snapshot-1",
            )

    def test_composite_query_defaults_are_stable(self) -> None:
        self.assertEqual(GovernmentQuery(), GovernmentQuery())


if __name__ == "__main__":
    unittest.main()

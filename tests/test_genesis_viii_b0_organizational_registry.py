from __future__ import annotations

import unittest

from core.government import (
    AuthorityLevel,
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    Department,
    GovernmentQuery,
    InMemoryGovernmentRegistry,
    LifecycleState,
    ObjectQuery,
    OrganizationalRelationship,
    RelationshipKind,
    bootstrap_government,
)
from core.government.registry.exceptions import (
    DuplicateObjectError,
    TransactionError,
)


class OrganizationalRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = InMemoryGovernmentRegistry()
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

    def test_register_query_and_relationship(self) -> None:
        from core.government import Directorate

        directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
            lifecycle=LifecycleState.ACTIVE,
        )
        department = Department(
            identifier=self.assimilation,
            title="Assimilation Department",
            mission="Assimilate governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            lifecycle=LifecycleState.ACTIVE,
            owner=self.knowledge,
        )

        self.registry.register_object(directorate)
        self.registry.register_object(department)
        relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )
        self.registry.register_relationship(relationship)

        snapshot = self.registry.query(
            GovernmentQuery(
                objects=ObjectQuery(
                    kinds=(
                        ConstitutionalObjectKind.DIRECTORATE,
                        ConstitutionalObjectKind.DEPARTMENT,
                    )
                )
            )
        )
        self.assertEqual(len(snapshot.objects), 2)
        self.assertEqual(snapshot.relationships, (relationship,))

    def test_duplicate_object_is_rejected(self) -> None:
        from core.government import Directorate

        directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
        )
        self.registry.register_object(directorate)
        with self.assertRaises(DuplicateObjectError):
            self.registry.register_object(directorate)

    def test_transaction_rolls_back_on_exception(self) -> None:
        from core.government import Directorate

        directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
        )

        with self.assertRaises(RuntimeError):
            with self.registry.transaction():
                self.registry.register_object(directorate)
                raise RuntimeError("abort")

        self.assertEqual(self.registry._objects, {})

    def test_remove_object_with_relationship_is_blocked(self) -> None:
        from core.government import Directorate

        directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
        )
        department = Department(
            identifier=self.assimilation,
            title="Assimilation Department",
            mission="Assimilate governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            owner=self.knowledge,
        )
        self.registry.register_object(directorate)
        self.registry.register_object(department)
        self.registry.register_relationship(
            OrganizationalRelationship(
                self.knowledge,
                RelationshipKind.OWNS,
                self.assimilation,
            )
        )
        with self.assertRaises(TransactionError):
            self.registry.remove_object(self.knowledge)

    def test_snapshot_restore_and_fingerprint(self) -> None:
        result = bootstrap_government()
        snapshot = result.registry.snapshot("baseline")
        fingerprint = result.registry.fingerprint()

        restored = InMemoryGovernmentRegistry()
        restored.restore(snapshot)

        self.assertEqual(restored.fingerprint(), fingerprint)

    def test_bootstrap_is_deterministic(self) -> None:
        first = bootstrap_government()
        second = bootstrap_government()
        self.assertEqual(first.object_count, second.object_count)
        self.assertEqual(first.relationship_count, second.relationship_count)
        self.assertEqual(first.fingerprint, second.fingerprint)


if __name__ == "__main__":
    unittest.main()

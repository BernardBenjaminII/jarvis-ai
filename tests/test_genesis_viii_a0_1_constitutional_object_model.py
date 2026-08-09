
from __future__ import annotations
import unittest
from core.government.models import (
    AuthorityLevel, ConstitutionalIdentifier, ConstitutionalObjectKind,
    Department, Directorate, HealthState, LifecycleState, ReadinessState,
    object_from_dict,
)

class ConstitutionalObjectModelTests(unittest.TestCase):
    def test_identifier_round_trip(self):
        value = "department:knowledge:assimilation"
        identifier = ConstitutionalIdentifier.parse(value)
        self.assertEqual(identifier.value, value)

    def test_wrong_identifier_kind_is_rejected(self):
        identifier = ConstitutionalIdentifier(
            ConstitutionalObjectKind.SERVICE, "knowledge", "assimilation"
        )
        with self.assertRaises(ValueError):
            Department(
                identifier=identifier,
                title="Assimilation",
                mission="Assimilate knowledge.",
                authority=AuthorityLevel.DEPARTMENT,
            )

    def test_object_serialization_round_trip(self):
        owner = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DIRECTORATE, "government", "knowledge"
        )
        department = Department(
            identifier=ConstitutionalIdentifier(
                ConstitutionalObjectKind.DEPARTMENT, "knowledge", "assimilation"
            ),
            title="Assimilation Department",
            mission="Transform admitted sources into governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            lifecycle=LifecycleState.ACTIVE,
            health=HealthState.HEALTHY,
            readiness=ReadinessState.READY,
            owner=owner,
            constitutional_basis=("GOA-0000 Article XXVI",),
            tags=("Knowledge", "Assimilation"),
            metadata={"version": "1"},
        )
        restored = object_from_dict(department.to_dict())
        self.assertEqual(restored, department)
        self.assertEqual(restored.fingerprint, department.fingerprint)

    def test_fingerprint_is_deterministic(self):
        kwargs = dict(
            identifier=ConstitutionalIdentifier(
                ConstitutionalObjectKind.DIRECTORATE, "government", "engineering"
            ),
            title="Engineering Directorate",
            mission="Design, construct, verify, and maintain capability.",
            authority=AuthorityLevel.DIRECTORATE,
        )
        self.assertEqual(Directorate(**kwargs).fingerprint, Directorate(**kwargs).fingerprint)

    def test_lifecycle_transition_contract(self):
        directorate = Directorate(
            identifier=ConstitutionalIdentifier(
                ConstitutionalObjectKind.DIRECTORATE, "government", "operations"
            ),
            title="Operations Directorate",
            mission="Execute organizational missions.",
            authority=AuthorityLevel.DIRECTORATE,
            lifecycle=LifecycleState.CERTIFIED,
        )
        self.assertTrue(directorate.can_transition_to(LifecycleState.ACTIVE))
        self.assertFalse(directorate.can_transition_to(LifecycleState.DRAFT))

    def test_self_ownership_is_rejected(self):
        identifier = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DIRECTORATE, "government", "executive"
        )
        with self.assertRaises(ValueError):
            Directorate(
                identifier=identifier,
                title="Executive Directorate",
                mission="Coordinate the organization.",
                authority=AuthorityLevel.DIRECTORATE,
                owner=identifier,
            )

if __name__ == "__main__":
    unittest.main()

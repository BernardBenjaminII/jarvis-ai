from __future__ import annotations

import json
import unittest

from core.government import (
    AuthorityLevel,
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    Department,
    Directorate,
    GovernmentCodec,
    GovernmentEnvelope,
    GovernmentFingerprintError,
    LifecycleState,
    OrganizationalGraph,
    OrganizationalRelationship,
    RelationshipKind,
    UnsupportedGovernmentSchemaError,
)


class CanonicalGovernmentSerializationTests(unittest.TestCase):
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

    def test_object_round_trip(self) -> None:
        department = Department(
            identifier=self.assimilation,
            title="Assimilation Department",
            mission="Transform admitted sources into governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            lifecycle=LifecycleState.ACTIVE,
            owner=self.knowledge,
            metadata={"version": "1"},
        )
        serialized = GovernmentCodec.dumps(
            department,
            metadata={"producer": "Genesis VIII-A0-3"},
        )
        restored = GovernmentCodec.loads(serialized)
        self.assertEqual(restored, department)

    def test_relationship_round_trip(self) -> None:
        relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )
        restored = GovernmentCodec.loads(GovernmentCodec.dumps(relationship))
        self.assertEqual(restored, relationship)

    def test_graph_round_trip(self) -> None:
        relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )
        graph = OrganizationalGraph.create((relationship,))
        restored = GovernmentCodec.loads(GovernmentCodec.dumps(graph))
        self.assertEqual(restored, graph)
        self.assertEqual(restored.fingerprint, graph.fingerprint)

    def test_canonical_output_is_deterministic(self) -> None:
        relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
            metadata={"z": "last", "a": "first"},
        )
        first = GovernmentCodec.dumps(
            relationship,
            metadata={"z": "last", "a": "first"},
        )
        second = GovernmentCodec.dumps(
            relationship,
            metadata={"a": "first", "z": "last"},
        )
        self.assertEqual(first, second)

    def test_tampering_is_detected(self) -> None:
        relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )
        payload = json.loads(GovernmentCodec.dumps(relationship))
        payload["payload"]["kind"] = "supports"

        with self.assertRaises(GovernmentFingerprintError):
            GovernmentEnvelope.from_dict(payload)

    def test_unsupported_schema_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedGovernmentSchemaError):
            GovernmentEnvelope(
                payload_type="constitutional_object",
                payload={"example": True},
                schema_version="99.0.0",
            )

    def test_envelope_fingerprint_is_stable(self) -> None:
        first = GovernmentEnvelope(
            payload_type="constitutional_object",
            payload={"b": 2, "a": 1},
            metadata={"z": "last", "a": "first"},
        )
        second = GovernmentEnvelope(
            payload_type="constitutional_object",
            payload={"a": 1, "b": 2},
            metadata={"a": "first", "z": "last"},
        )
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(first.to_json(), second.to_json())

    def test_object_fingerprint_survives_envelope_round_trip(self) -> None:
        directorate = Directorate(
            identifier=self.knowledge,
            title="Knowledge Directorate",
            mission="Steward organizational knowledge.",
            authority=AuthorityLevel.DIRECTORATE,
        )
        restored = GovernmentCodec.loads(GovernmentCodec.dumps(directorate))
        self.assertEqual(restored.fingerprint, directorate.fingerprint)


if __name__ == "__main__":
    unittest.main()

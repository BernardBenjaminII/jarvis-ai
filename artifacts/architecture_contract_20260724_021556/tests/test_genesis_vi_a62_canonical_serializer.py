"""Tests for Genesis VI-A6.2 canonical snapshot serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import unittest
from uuid import UUID

from core.executive.persistence import (
    CanonicalSnapshotSerializer,
    CanonicalizationError,
    PersistenceRecordKind,
    SchemaIdentity,
)


@dataclass(frozen=True)
class FixtureSnapshot:
    session_id: str
    sequence: int
    created_at: datetime
    record_kind: PersistenceRecordKind
    labels: tuple[str, ...]


class CanonicalSerializerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.serializer = CanonicalSnapshotSerializer()
        self.fixture = FixtureSnapshot(
            session_id="session-001",
            sequence=7,
            created_at=datetime(
                2026, 7, 22, 19, 30, tzinfo=timezone.utc
            ),
            record_kind=PersistenceRecordKind.SESSION_SNAPSHOT,
            labels=("executive", "certified"),
        )

    def test_identical_state_produces_identical_bytes(self) -> None:
        first = self.serializer.dumps(self.fixture)
        second = self.serializer.dumps(self.fixture)

        self.assertEqual(first.payload, second.payload)
        self.assertEqual(
            first.integrity.digest,
            second.integrity.digest,
        )

    def test_mapping_order_does_not_change_payload(self) -> None:
        first = self.serializer.dumps({"b": 2, "a": 1})
        second = self.serializer.dumps({"a": 1, "b": 2})

        self.assertEqual(first.payload, second.payload)

    def test_payload_is_compact_canonical_utf8(self) -> None:
        snapshot = self.serializer.dumps({"message": "سلام"})

        self.assertNotIn(b" ", snapshot.payload)
        self.assertEqual(snapshot.encoding, "utf-8")
        self.assertIn("سلام", snapshot.text)

    def test_digest_verification_detects_tampering(self) -> None:
        snapshot = self.serializer.dumps(self.fixture)

        self.assertTrue(self.serializer.verify(snapshot))

        altered = type(snapshot)(
            schema=snapshot.schema,
            payload=snapshot.payload + b"x",
            integrity=snapshot.integrity,
        )
        self.assertFalse(self.serializer.verify(altered))

    def test_loads_validates_schema(self) -> None:
        snapshot = self.serializer.dumps(
            self.fixture,
            schema=SchemaIdentity(version=1),
        )
        document = self.serializer.loads(snapshot.payload)

        self.assertEqual(
            document["schema"],
            {
                "name": "jarvis.executive.persistence",
                "version": 1,
            },
        )

    def test_datetime_is_normalized_to_utc(self) -> None:
        value = datetime(
            2026,
            7,
            22,
            21,
            30,
            tzinfo=timezone.utc,
        )
        snapshot = self.serializer.dumps({"when": value})

        self.assertIn("2026-07-22T21:30:00.000000Z", snapshot.text)

    def test_uuid_is_serialized_stably(self) -> None:
        value = UUID("12345678-1234-5678-1234-567812345678")
        first = self.serializer.dumps({"id": value})
        second = self.serializer.dumps({"id": value})

        self.assertEqual(first.payload, second.payload)

    def test_set_order_is_deterministic(self) -> None:
        first = self.serializer.dumps({"items": {"c", "a", "b"}})
        second = self.serializer.dumps({"items": {"b", "c", "a"}})

        self.assertEqual(first.payload, second.payload)

    def test_naive_datetime_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            self.serializer.dumps(
                {"when": datetime(2026, 7, 22, 21, 30)}
            )

    def test_non_string_mapping_key_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            self.serializer.dumps({1: "invalid"})


if __name__ == "__main__":
    unittest.main()

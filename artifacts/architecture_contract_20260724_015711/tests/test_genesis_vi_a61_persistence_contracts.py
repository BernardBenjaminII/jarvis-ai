"""Tests for Genesis VI-A6.1 persistence contracts."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from core.executive.persistence import (
    CheckpointDescriptor,
    CheckpointReason,
    IntegrityMetadata,
    MigrationPath,
    PERSISTENCE_SCHEMA_NAME,
    PERSISTENCE_SCHEMA_VERSION,
    PersistenceEnvelope,
    PersistenceIntegrityStatus,
    PersistenceRecordKind,
    RecoveryRequest,
    SchemaIdentity,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
DIGEST = "a" * 64


class PersistenceContractTests(unittest.TestCase):
    def test_schema_identity_has_stable_canonical_name(self) -> None:
        schema = SchemaIdentity()

        self.assertEqual(schema.name, PERSISTENCE_SCHEMA_NAME)
        self.assertEqual(schema.version, PERSISTENCE_SCHEMA_VERSION)
        self.assertEqual(
            schema.canonical,
            "jarvis.executive.persistence@1",
        )

    def test_schema_version_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            SchemaIdentity(version=0)

    def test_integrity_metadata_normalizes_sha256(self) -> None:
        integrity = IntegrityMetadata(
            algorithm="SHA256",
            digest="A" * 64,
            status=PersistenceIntegrityStatus.VERIFIED,
        )

        self.assertEqual(integrity.algorithm, "sha256")
        self.assertEqual(integrity.digest, DIGEST)
        self.assertIs(
            integrity.status,
            PersistenceIntegrityStatus.VERIFIED,
        )

    def test_invalid_digest_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IntegrityMetadata(
                algorithm="sha256",
                digest="not-a-digest",
            )

    def test_envelope_freezes_sorted_metadata(self) -> None:
        envelope = PersistenceEnvelope(
            record_id="record-001",
            record_kind=PersistenceRecordKind.SESSION_SNAPSHOT,
            schema=SchemaIdentity(),
            session_id="session-001",
            mission_id="mission-001",
            executive_id="victor",
            created_at=NOW,
            payload_size=128,
            integrity=IntegrityMetadata(
                algorithm="sha256",
                digest=DIGEST,
            ),
            metadata={"z": 1, "a": 2},
        )

        self.assertEqual(
            tuple(envelope.metadata),
            ("a", "z"),
        )
        with self.assertRaises(TypeError):
            envelope.metadata["x"] = 3

    def test_envelope_is_immutable(self) -> None:
        envelope = PersistenceEnvelope(
            record_id="record-001",
            record_kind=PersistenceRecordKind.CHECKPOINT,
            schema=SchemaIdentity(),
            session_id="session-001",
            mission_id="mission-001",
            executive_id="victor",
            created_at=NOW,
            payload_size=0,
            integrity=IntegrityMetadata(
                algorithm="sha256",
                digest=DIGEST,
            ),
        )

        with self.assertRaises(FrozenInstanceError):
            envelope.record_id = "changed"

    def test_checkpoint_descriptor_normalizes_tags(self) -> None:
        descriptor = CheckpointDescriptor(
            checkpoint_id="checkpoint-001",
            session_id="session-001",
            sequence=1,
            reason=CheckpointReason.MANUAL,
            record_id="record-001",
            created_at=NOW,
            tags=(" beta ", "alpha", "alpha", ""),
        )

        self.assertEqual(descriptor.tags, ("alpha", "beta"))

    def test_checkpoint_sequence_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            CheckpointDescriptor(
                checkpoint_id="checkpoint-001",
                session_id="session-001",
                sequence=0,
                reason=CheckpointReason.MANUAL,
                record_id="record-001",
                created_at=NOW,
            )

    def test_migration_path_exposes_source_and_target(self) -> None:
        path = MigrationPath(
            schema_name=PERSISTENCE_SCHEMA_NAME,
            source_version=1,
            target_version=2,
            migration_id="migration-1-to-2",
        )

        self.assertEqual(path.source.version, 1)
        self.assertEqual(path.target.version, 2)

    def test_reverse_migration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MigrationPath(
                schema_name=PERSISTENCE_SCHEMA_NAME,
                source_version=2,
                target_version=1,
                migration_id="invalid",
            )

    def test_recovery_request_defaults_are_strict(self) -> None:
        request = RecoveryRequest(session_id="session-001")

        self.assertTrue(request.require_verified_integrity)
        self.assertFalse(request.allow_migration)
        self.assertEqual(request.target_schema, SchemaIdentity())


if __name__ == "__main__":
    unittest.main()

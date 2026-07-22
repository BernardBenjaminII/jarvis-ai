from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from core.executive.persistence import (
    CheckpointHistoryError,
    CheckpointIntegrityError,
    CheckpointNotFoundError,
    FileCheckpointRepository,
    StoragePathError,
)
from core.executive.persistence.checkpoint import decode_checkpoint, encode_checkpoint
from core.executive.persistence.storage import AtomicFileStorage


class GenesisVIA63CheckpointStoreTests(unittest.TestCase):
    def test_atomic_storage_confines_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            storage = AtomicFileStorage(temporary)
            with self.assertRaises(StoragePathError):
                storage.resolve("../escape.chk")

    def test_checkpoint_round_trip_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            checkpoint = repository.save(
                session_id="session-001",
                mission_id="mission-001",
                payload=b'{"state":"ready"}',
                schema_name="jarvis.executive.snapshot",
                schema_version=1,
                created_at=datetime(2026, 7, 22, 20, 0, tzinfo=timezone.utc),
                metadata={"reason": "test"},
            )
            encoded = encode_checkpoint(checkpoint)
            decoded = decode_checkpoint(encoded)
            self.assertEqual(decoded, checkpoint)
            self.assertEqual(encode_checkpoint(decoded), encoded)

    def test_repository_assigns_monotonic_sequences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            first = repository.save(
                session_id="session-001",
                payload=b"one",
                schema_name="snapshot",
                schema_version=1,
            )
            second = repository.save(
                session_id="session-001",
                payload=b"two",
                schema_name="snapshot",
                schema_version=1,
            )
            self.assertEqual(first.sequence, 1)
            self.assertEqual(second.sequence, 2)
            self.assertEqual(
                second.parent_checkpoint_sha256,
                first.checkpoint_sha256,
            )

    def test_latest_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            self.assertIsNone(repository.latest("session-001"))
            for value in (b"one", b"two", b"three"):
                repository.save(
                    session_id="session-001",
                    payload=value,
                    schema_name="snapshot",
                    schema_version=1,
                )
            latest = repository.latest("session-001")
            self.assertIsNotNone(latest)
            self.assertEqual(latest.payload, b"three")
            self.assertEqual(
                [item.sequence for item in repository.history("session-001")],
                [1, 2, 3],
            )

    def test_load_missing_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            with self.assertRaises(CheckpointNotFoundError):
                repository.load("session-001", 1)

    def test_payload_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            repository.save(
                session_id="session-001",
                payload=b"trusted",
                schema_name="snapshot",
                schema_version=1,
            )
            path = (
                Path(temporary)
                / "sessions"
                / "session-001"
                / "00000001.chk"
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            payload = bytearray.fromhex(document["payload_hex"])
            payload[0] ^= 0x01
            document["payload_hex"] = bytes(payload).hex()
            path.write_text(
                json.dumps(
                    document,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(CheckpointIntegrityError):
                repository.load("session-001", 1)

    def test_manifest_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            repository.save(
                session_id="session-001",
                payload=b"trusted",
                schema_name="snapshot",
                schema_version=1,
            )
            path = (
                Path(temporary)
                / "sessions"
                / "session-001"
                / "00000001.chk"
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            document["metadata"] = {"tampered": "true"}
            path.write_text(
                json.dumps(
                    document,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(CheckpointIntegrityError):
                repository.load("session-001", 1)

    def test_sequence_gap_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            repository.save(
                session_id="session-001",
                payload=b"one",
                schema_name="snapshot",
                schema_version=1,
            )
            repository.save(
                session_id="session-001",
                payload=b"two",
                schema_name="snapshot",
                schema_version=1,
            )
            source = (
                Path(temporary)
                / "sessions"
                / "session-001"
                / "00000002.chk"
            )
            source.rename(source.with_name("00000003.chk"))
            with self.assertRaises(CheckpointHistoryError):
                repository.history("session-001")

    def test_archive_moves_verified_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            repository.save(
                session_id="session-001",
                payload=b"one",
                schema_name="snapshot",
                schema_version=1,
            )
            archived = repository.archive("session-001")
            self.assertTrue(archived.is_dir())
            self.assertIsNone(repository.latest("session-001"))
            self.assertTrue((archived / "00000001.chk").is_file())

    def test_index_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            repository.save(
                session_id="session-001",
                payload=b"one",
                schema_name="snapshot",
                schema_version=1,
            )
            index = (
                Path(temporary)
                / "sessions"
                / "session-001"
                / "index.json"
            )
            self.assertTrue(index.is_file())
            self.assertIn('"sequence":1', index.read_text(encoding="utf-8"))

    def test_session_enumeration_is_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = FileCheckpointRepository(temporary)
            for session_id in ("session-b", "session-a"):
                repository.save(
                    session_id=session_id,
                    payload=b"state",
                    schema_name="snapshot",
                    schema_version=1,
                )
            self.assertEqual(
                repository.session_ids(),
                ("session-a", "session-b"),
            )


if __name__ == "__main__":
    unittest.main()

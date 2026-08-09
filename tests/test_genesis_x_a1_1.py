from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.knowledge_catalog.production_materialization.checkpoint import (
    CheckpointStore,
)
from core.knowledge_catalog.production_materialization.models import (
    MaterializationStage,
    WorkItem,
)
from core.knowledge_catalog.production_materialization.reliability import (
    ReliableSQLite,
    SQLiteReliabilityPolicy,
    is_transient_lock_error,
)


class GenesisXA11Tests(unittest.TestCase):
    def test_lock_error_classification(self):
        self.assertTrue(
            is_transient_lock_error(
                sqlite3.OperationalError(
                    "database is locked"
                )
            )
        )
        self.assertFalse(
            is_transient_lock_error(
                sqlite3.OperationalError(
                    "no such table"
                )
            )
        )

    def test_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "test.sqlite"
            sqlite3.connect(database).close()
            reliable = ReliableSQLite(
                database,
                SQLiteReliabilityPolicy(
                    retry_attempts=3,
                    initial_backoff_seconds=0,
                    maximum_backoff_seconds=0,
                    jitter_fraction=0,
                ),
            )
            attempts = {"count": 0}

            def operation():
                attempts["count"] += 1
                if attempts["count"] < 3:
                    raise sqlite3.OperationalError(
                        "database is locked"
                    )
                return "ok"

            self.assertEqual(
                reliable.run_with_retry(
                    operation
                ),
                "ok",
            )
            self.assertEqual(
                attempts["count"],
                3,
            )

    def test_wal_and_busy_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "test.sqlite"
            sqlite3.connect(database).close()
            reliable = ReliableSQLite(
                database,
                SQLiteReliabilityPolicy(
                    busy_timeout_ms=1234,
                ),
            )
            result = (
                reliable.configure_runtime_database()
            )
            self.assertEqual(
                result["journal_mode"].casefold(),
                "wal",
            )
            self.assertEqual(
                result["busy_timeout_ms"],
                1234,
            )

    def test_incomplete_state_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            store = CheckpointStore(
                Path(temp) / "checkpoint.sqlite"
            )
            item = WorkItem(
                "id:1",
                "/tmp/a.txt",
                "A",
                None,
                ".txt",
            )
            store.register((item,))
            store.set_stage(
                item.candidate_id,
                MaterializationStage.CHUNKED,
                "chunked",
            )
            recovered = (
                store.recover_incomplete_states()
            )
            self.assertEqual(
                recovered["CHUNKED"],
                1,
            )
            self.assertEqual(
                store.counts()["VALIDATED"],
                1,
            )

    def test_lock_failure_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            store = CheckpointStore(
                Path(temp) / "checkpoint.sqlite"
            )
            item = WorkItem(
                "id:1",
                "/tmp/a.txt",
                "A",
                None,
                ".txt",
            )
            store.register((item,))
            store.set_stage(
                item.candidate_id,
                MaterializationStage.FAILED,
                "OperationalError: database is locked",
            )
            self.assertEqual(
                store.recover_transient_lock_failures(),
                1,
            )
            self.assertEqual(
                store.counts()["VALIDATED"],
                1,
            )


if __name__ == "__main__":
    unittest.main()

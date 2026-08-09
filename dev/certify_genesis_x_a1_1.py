from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

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
)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        database = root / "runtime.sqlite"
        sqlite3.connect(database).close()

        reliable = ReliableSQLite(
            database,
            SQLiteReliabilityPolicy(
                busy_timeout_ms=2500,
                retry_attempts=3,
                initial_backoff_seconds=0,
                maximum_backoff_seconds=0,
                jitter_fraction=0,
            ),
        )
        configuration = (
            reliable.configure_runtime_database()
        )

        attempts = {"count": 0}

        def operation():
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise sqlite3.OperationalError(
                    "database is locked"
                )
            return "ok"

        retry_result = (
            reliable.run_with_retry(
                operation
            )
        )

        store = CheckpointStore(
            root / "checkpoint.sqlite"
        )
        chunked = WorkItem(
            "id:1",
            "/tmp/a.txt",
            "A",
            None,
            ".txt",
        )
        locked = WorkItem(
            "id:2",
            "/tmp/b.txt",
            "B",
            None,
            ".txt",
        )
        store.register((chunked, locked))
        store.set_stage(
            chunked.candidate_id,
            MaterializationStage.CHUNKED,
            "chunked",
        )
        store.set_stage(
            locked.candidate_id,
            MaterializationStage.FAILED,
            "OperationalError: database is locked",
        )

        incomplete = (
            store.recover_incomplete_states()
        )
        lock_failures = (
            store.recover_transient_lock_failures()
        )

        checks = {
            "wal_enabled": (
                configuration[
                    "journal_mode"
                ].casefold()
                == "wal"
            ),
            "busy_timeout": (
                configuration[
                    "busy_timeout_ms"
                ]
                == 2500
            ),
            "lock_retry": (
                retry_result == "ok"
                and attempts["count"] == 2
            ),
            "chunked_recovered": (
                incomplete.get("CHUNKED")
                == 1
            ),
            "lock_failure_recovered": (
                lock_failures == 1
            ),
            "validated_count": (
                store.counts().get(
                    "VALIDATED"
                )
                == 2
            ),
            "checkpoint_separate": (
                store.path != database
            ),
        }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    print("=" * 76)
    print("GENESIS X-A1.1 — SQLITE RELIABILITY AND RESUME REPAIR")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print(
        "Overall status  :",
        "EXCELLENT" if not failed else "FAILED",
    )

    if failed:
        print(
            "Failed checks   :",
            ", ".join(failed),
        )

    print("=" * 76)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

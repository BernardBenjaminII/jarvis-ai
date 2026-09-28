#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-B DOCUMENT SAFETY VERIFICATION'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/__init__.py \
    knowledge_engine/assimilation/schema.py \
    knowledge_engine/assimilation/dispatch.py \
    knowledge_engine/assimilation/mission.py \
    knowledge_engine/assimilation/planner.py \
    knowledge_engine/assimilation/director.py \
    knowledge_engine/assimilation/runner.py \
    knowledge_engine/assimilation/single_document.py \
    knowledge_engine/assimilation_cli.py

"${PYTHON_BIN}" - <<'PY'
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation import (
    AssimilationDirector,
    AssimilationRunner,
)
from knowledge_engine.storage.database import KnowledgeDatabase


def create_test_database(path: Path) -> None:
    connection = sqlite3.connect(path)

    connection.executescript(
        """
        CREATE TABLE knowledge_registry (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            assimilation_state TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE knowledge_assimilation_queue (
            object_uuid TEXT PRIMARY KEY,
            queue_state TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE document_text (
            document_path TEXT PRIMARY KEY,
            extractor TEXT,
            text TEXT,
            checksum TEXT,
            status TEXT,
            error TEXT,
            extracted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            source_page INTEGER,
            structure_title TEXT
        );
        """
    )

    connection.commit()
    connection.close()


def add_document(
    database_path: Path,
    *,
    object_uuid: str,
    object_path: Path,
) -> None:
    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        INSERT INTO knowledge_registry (
            object_uuid,
            object_path,
            object_type,
            lifecycle_state,
            assimilation_state
        )
        VALUES (?, ?, 'single_document', 'validated', 'queued')
        """,
        (
            object_uuid,
            str(object_path),
        ),
    )

    connection.execute(
        """
        INSERT INTO knowledge_assimilation_queue (
            object_uuid,
            queue_state
        )
        VALUES (?, 'queued')
        """,
        (object_uuid,),
    )

    connection.commit()
    connection.close()


with tempfile.TemporaryDirectory(prefix="jarvis-phase-6b-") as temporary:
    root = Path(temporary)
    database_path = root / "catalog.sqlite"

    create_test_database(database_path)

    valid_document = root / "valid.txt"
    valid_document.write_text(
        ("JARVIS failure-safe assimilation verification. " * 200),
        encoding="utf-8",
    )

    missing_document = root / "missing.txt"

    add_document(
        database_path,
        object_uuid="valid-document",
        object_path=valid_document,
    )

    add_document(
        database_path,
        object_uuid="missing-document",
        object_path=missing_document,
    )

    # Make queue ordering explicit and deterministic. The valid document must
    # be selected first so the suite tests success before retry exhaustion.
    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        UPDATE knowledge_registry
        SET updated_at='2026-01-01 00:00:00'
        WHERE object_uuid='valid-document'
        """
    )

    connection.execute(
        """
        UPDATE knowledge_assimilation_queue
        SET updated_at='2026-01-01 00:00:00'
        WHERE object_uuid='valid-document'
        """
    )

    connection.execute(
        """
        UPDATE knowledge_registry
        SET updated_at='2026-01-01 00:01:00'
        WHERE object_uuid='missing-document'
        """
    )

    connection.execute(
        """
        UPDATE knowledge_assimilation_queue
        SET updated_at='2026-01-01 00:01:00'
        WHERE object_uuid='missing-document'
        """
    )

    connection.commit()
    connection.close()

    db = KnowledgeDatabase(database_path)
    runner = AssimilationRunner(
        db,
        default_max_attempts=2,
    )
    director = AssimilationDirector(
        db,
        runner=runner,
    )

    mission = director.plan(
        limit=1,
        object_types=["single_document"],
    )

    assert mission.total_items == 1
    assert mission.executable_items == 1
    assert mission.items[0].object_uuid == "valid-document"

    director.execute(mission)

    assert mission.processed == 1
    assert mission.failed == 0
    assert mission.status.value == "completed"

    with db.connect() as connection:
        registry = connection.execute(
            """
            SELECT lifecycle_state, assimilation_state
            FROM knowledge_registry
            WHERE object_uuid='valid-document'
            """
        ).fetchone()

        queue = connection.execute(
            """
            SELECT queue_state, attempt_count
            FROM knowledge_assimilation_queue
            WHERE object_uuid='valid-document'
            """
        ).fetchone()

        document_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM document_text
            WHERE document_path=?
            """,
            (str(valid_document),),
        ).fetchone()[0]

        chunk_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            WHERE document_path=?
            """,
            (str(valid_document),),
        ).fetchone()[0]

        attempt = connection.execute(
            """
            SELECT attempt_state
            FROM knowledge_assimilation_attempts
            WHERE object_uuid='valid-document'
            """
        ).fetchone()


    print("\n=== REGISTRY ===")
    print(dict(registry) if registry else None)

    print("\n=== QUEUE ===")
    print(dict(queue) if queue else None)

    print("\n=== DOCUMENT COUNT ===")
    print(document_count)

    print("\n=== CHUNK COUNT ===")
    print(chunk_count)

    print("\n=== ATTEMPT ROW ===")
    print(dict(attempt) if attempt else None)

    attempt_rows = connection.execute("""
    SELECT
        attempt_id,
        object_uuid,
        attempt_number,
        attempt_state,
        error_type,
        error_message
    FROM knowledge_assimilation_attempts
    ORDER BY attempt_id
    """).fetchall()

    print("\n=== ALL ATTEMPTS ===")
    for row in attempt_rows:
        print(dict(row))

    assert registry[0] == "chunked", f"registry={dict(registry)}"
    assert registry[1] == "ready_for_embedding", f"registry={dict(registry)}"
    assert queue[0] == "completed", f"queue={dict(queue)}"
    assert queue[1] == 1, f"queue={dict(queue)}"
    assert document_count == 1, f"document_count={document_count}"
    assert chunk_count > 0, f"chunk_count={chunk_count}"
    assert attempt[0] == "completed", f"attempt={dict(attempt) if attempt else None}"

    first_failure = runner.run_one_single_document(
        expected_object_uuid="missing-document",
    )

    assert first_failure["failed"] == 1, first_failure
    assert first_failure["retry_exhausted"] is False, first_failure
    assert first_failure["queue_state"] == "queued", first_failure

    second_failure = runner.run_one_single_document(
        expected_object_uuid="missing-document",
    )

    assert second_failure["failed"] == 1, second_failure
    assert second_failure["retry_exhausted"] is True, second_failure
    assert second_failure["queue_state"] == "failed", second_failure

    with db.connect() as connection:
        registry = connection.execute(
            """
            SELECT lifecycle_state, assimilation_state
            FROM knowledge_registry
            WHERE object_uuid='missing-document'
            """
        ).fetchone()

        queue = connection.execute(
            """
            SELECT queue_state, attempt_count, last_error
            FROM knowledge_assimilation_queue
            WHERE object_uuid='missing-document'
            """
        ).fetchone()

        attempts = connection.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_assimilation_attempts
            WHERE object_uuid='missing-document'
              AND attempt_state='failed'
            """
        ).fetchone()[0]

    assert registry[0] == "assimilation_failed"
    assert registry[1] == "failed"
    assert queue[0] == "failed"
    assert queue[1] == 2
    assert "FileNotFoundError" in queue[2]
    assert attempts == 2

    requeue = runner.requeue_failed_documents(
        limit=1,
        reset_attempts=True,
    )

    assert requeue["requeued"] == 1

    with db.connect() as connection:
        queue = connection.execute(
            """
            SELECT queue_state, attempt_count
            FROM knowledge_assimilation_queue
            WHERE object_uuid='missing-document'
            """
        ).fetchone()

    assert queue[0] == "queued"
    assert queue[1] == 0

print("[PASS] Successful document assimilation")
print("[PASS] Atomic document state transitions")
print("[PASS] Attempt journal creation")
print("[PASS] Failure diagnostics")
print("[PASS] Retry limit enforcement")
print("[PASS] Explicit failed-document requeue")
print("[PASS] Director bounded execution")
PY

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

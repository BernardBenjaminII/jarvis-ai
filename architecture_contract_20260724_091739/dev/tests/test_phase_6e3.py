"""
Regression verification for JARVIS Gen 2 Phase VI-E3.

All writes occur in a temporary SQLite catalog.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.attempts import (
    AttemptJournalService,
)
from knowledge_engine.storage.database import KnowledgeDatabase


def create_database(path: Path) -> None:
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

    ensure_assimilation_runtime_schema(connection)
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


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-6e3-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"

        create_database(database_path)

        db = KnowledgeDatabase(database_path)
        service = AttemptJournalService()

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            started = service.start_attempt(
                conn=conn,
                object_uuid="manual-object",
                object_path="/tmp/manual-object.txt",
                object_type="single_document",
                handler_name="phase_6e3_test",
                attempt_number=1,
            )

            assert started.attempt_id > 0
            assert started.attempt_state == "processing"

            completed = service.complete_attempt(
                conn=conn,
                attempt_id=started.attempt_id,
                text_chars=100,
                chunk_count=4,
                checksum="abc123",
            )

            assert completed.applied
            assert completed.attempt_state == "completed"

            conn.commit()

        with db.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    attempt_state,
                    text_chars,
                    chunk_count,
                    checksum,
                    error_type,
                    error_message
                FROM knowledge_assimilation_attempts
                WHERE attempt_id=?
                """,
                (started.attempt_id,),
            ).fetchone()

        assert row[0] == "completed", row
        assert row[1] == 100, row
        assert row[2] == 4, row
        assert row[3] == "abc123", row
        assert row[4] is None, row
        assert row[5] is None, row

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            failed_start = service.start_attempt(
                conn=conn,
                object_uuid="failed-object",
                object_path="/tmp/failed-object.txt",
                object_type="single_document",
                handler_name="phase_6e3_test",
                attempt_number=1,
            )

            failed = service.fail_attempt(
                conn=conn,
                attempt_id=failed_start.attempt_id,
                error_type="RuntimeError",
                error_message="controlled failure",
            )

            assert failed.applied
            conn.commit()

        with db.connect() as conn:
            row = conn.execute(
                """
                SELECT attempt_state, error_type, error_message
                FROM knowledge_assimilation_attempts
                WHERE attempt_id=?
                """,
                (failed_start.attempt_id,),
            ).fetchone()

        assert row[0] == "failed", row
        assert row[1] == "RuntimeError", row
        assert row[2] == "controlled failure", row

        valid_document = root / "valid.txt"
        valid_document.write_text(
            "Attempt journal integration verification. " * 200,
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

        runner = AssimilationRunner(
            db,
            default_max_attempts=2,
            attempt_service=service,
        )

        success = runner.run_one_single_document(
            expected_object_uuid="valid-document",
        )

        assert success["processed"] == 1, success
        assert success["failed"] == 0, success

        failure = runner.run_one_single_document(
            expected_object_uuid="missing-document",
        )

        assert failure["processed"] == 0, failure
        assert failure["failed"] == 1, failure
        assert failure["retry_exhausted"] is False, failure

        with db.connect() as conn:
            success_attempt = conn.execute(
                """
                SELECT attempt_state, text_chars, chunk_count, checksum
                FROM knowledge_assimilation_attempts
                WHERE object_uuid='valid-document'
                ORDER BY attempt_id DESC
                LIMIT 1
                """
            ).fetchone()

            failure_attempt = conn.execute(
                """
                SELECT attempt_state, error_type, error_message
                FROM knowledge_assimilation_attempts
                WHERE object_uuid='missing-document'
                ORDER BY attempt_id DESC
                LIMIT 1
                """
            ).fetchone()

        assert success_attempt[0] == "completed", success_attempt
        assert success_attempt[1] > 0, success_attempt
        assert success_attempt[2] > 0, success_attempt
        assert success_attempt[3], success_attempt

        assert failure_attempt[0] == "failed", failure_attempt
        assert failure_attempt[1] == "FileNotFoundError", failure_attempt
        assert "does not exist" in failure_attempt[2], failure_attempt

    print("[PASS] Attempt creation")
    print("[PASS] Attempt completion statistics")
    print("[PASS] Attempt failure diagnostics")
    print("[PASS] Runner delegates successful attempt updates")
    print("[PASS] Runner delegates failed attempt updates")
    print("[PASS] Existing retry behavior preserved")


if __name__ == "__main__":
    main()

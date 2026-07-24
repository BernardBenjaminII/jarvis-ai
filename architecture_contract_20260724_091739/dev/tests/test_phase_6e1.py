"""
Regression verification for JARVIS Gen 2 Phase VI-E1.

All verification uses a temporary SQLite database.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
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
        prefix="jarvis-phase-6e1-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"
        document_path = root / "document.txt"

        document_path.write_text(
            "JARVIS state-service verification. " * 200,
            encoding="utf-8",
        )

        create_database(database_path)

        add_document(
            database_path,
            object_uuid="document-001",
            object_path=document_path,
        )

        db = KnowledgeDatabase(database_path)
        state_service = AssimilationStateService()

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            claim = state_service.claim_document(
                conn=conn,
                object_uuid="document-001",
                attempt_number=1,
                max_attempts=3,
            )

            assert claim.applied, claim

            registry = conn.execute(
                """
                SELECT lifecycle_state, assimilation_state
                FROM knowledge_registry
                WHERE object_uuid='document-001'
                """
            ).fetchone()

            queue = conn.execute(
                """
                SELECT queue_state, attempt_count, max_attempts
                FROM knowledge_assimilation_queue
                WHERE object_uuid='document-001'
                """
            ).fetchone()

            assert registry[0] == "extracting", registry
            assert registry[1] == "processing", registry
            assert queue[0] == "processing", queue
            assert queue[1] == 1, queue
            assert queue[2] == 3, queue

            failure = state_service.mark_document_failure(
                conn=conn,
                object_uuid="document-001",
                error_text="RuntimeError: temporary test failure",
                retry_exhausted=False,
            )

            assert failure.applied, failure
            conn.commit()

        with db.connect() as conn:
            registry = conn.execute(
                """
                SELECT lifecycle_state, assimilation_state
                FROM knowledge_registry
                WHERE object_uuid='document-001'
                """
            ).fetchone()

            queue = conn.execute(
                """
                SELECT queue_state, last_error
                FROM knowledge_assimilation_queue
                WHERE object_uuid='document-001'
                """
            ).fetchone()

        assert registry[0] == "validated", registry
        assert registry[1] == "queued", registry
        assert queue[0] == "queued", queue
        assert "temporary test failure" in queue[1], queue

        runner = AssimilationRunner(
            db,
            default_max_attempts=2,
            state_service=state_service,
        )

        result = runner.run_one_single_document(
            expected_object_uuid="document-001",
        )

        assert result["processed"] == 1, result
        assert result["failed"] == 0, result

        with db.connect() as conn:
            registry = conn.execute(
                """
                SELECT lifecycle_state, assimilation_state
                FROM knowledge_registry
                WHERE object_uuid='document-001'
                """
            ).fetchone()

            queue = conn.execute(
                """
                SELECT queue_state
                FROM knowledge_assimilation_queue
                WHERE object_uuid='document-001'
                """
            ).fetchone()

            chunk_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM chunks
                WHERE document_path=?
                """,
                (str(document_path),),
            ).fetchone()[0]

        assert registry[0] == "chunked", registry
        assert registry[1] == "ready_for_embedding", registry
        assert queue[0] == "completed", queue
        assert chunk_count > 0, chunk_count

    print("[PASS] State-service processing claim")
    print("[PASS] State-service retry transition")
    print("[PASS] Queue diagnostics retained")
    print("[PASS] Runner delegates state transitions")
    print("[PASS] Existing document behavior preserved")


if __name__ == "__main__":
    main()

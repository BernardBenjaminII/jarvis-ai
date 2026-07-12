"""
Regression verification for JARVIS Gen 2 Phase VI-E2.

All writes occur in a temporary SQLite database.
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.persistence import (
    DocumentPersistenceService,
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
        prefix="jarvis-phase-6e2-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"
        document_path = root / "document.txt"

        create_database(database_path)

        db = KnowledgeDatabase(database_path)
        service = DocumentPersistenceService()

        initial_text = "Alpha Bravo Charlie"
        initial_checksum = hashlib.sha256(
            initial_text.encode("utf-8")
        ).hexdigest()

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            first = service.persist_document(
                conn=conn,
                document_path=str(document_path),
                text=initial_text,
                checksum=initial_checksum,
                chunks=[
                    "Alpha",
                    "Bravo",
                    "Charlie",
                ],
                extractor="phase_6e2_test",
            )

            assert first.persisted, first
            assert first.text_chars == len(initial_text), first
            assert first.chunk_count == 3, first

            conn.commit()

        with db.connect() as conn:
            text_row = conn.execute(
                """
                SELECT extractor, text, checksum, status, error
                FROM document_text
                WHERE document_path=?
                """,
                (str(document_path),),
            ).fetchone()

            chunk_rows = conn.execute(
                """
                SELECT chunk_index, text
                FROM chunks
                WHERE document_path=?
                ORDER BY chunk_index ASC
                """,
                (str(document_path),),
            ).fetchall()

        assert text_row[0] == "phase_6e2_test", text_row
        assert text_row[1] == initial_text, text_row
        assert text_row[2] == initial_checksum, text_row
        assert text_row[3] == "extracted", text_row
        assert text_row[4] is None, text_row

        assert [
            tuple(row)
            for row in chunk_rows
        ] == [
            (0, "Alpha"),
            (1, "Bravo"),
            (2, "Charlie"),
        ]

        replacement_text = "Delta Echo"
        replacement_checksum = hashlib.sha256(
            replacement_text.encode("utf-8")
        ).hexdigest()

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            replacement = service.persist_document(
                conn=conn,
                document_path=str(document_path),
                text=replacement_text,
                checksum=replacement_checksum,
                chunks=[
                    "Delta",
                    "Echo",
                ],
                extractor="phase_6e2_replacement",
            )

            assert replacement.persisted, replacement
            assert replacement.chunk_count == 2, replacement

            conn.commit()

        with db.connect() as conn:
            text_row = conn.execute(
                """
                SELECT extractor, text, checksum
                FROM document_text
                WHERE document_path=?
                """,
                (str(document_path),),
            ).fetchone()

            chunk_rows = conn.execute(
                """
                SELECT chunk_index, text
                FROM chunks
                WHERE document_path=?
                ORDER BY chunk_index ASC
                """,
                (str(document_path),),
            ).fetchall()

        assert text_row[0] == "phase_6e2_replacement", text_row
        assert text_row[1] == replacement_text, text_row
        assert text_row[2] == replacement_checksum, text_row

        assert [
            tuple(row)
            for row in chunk_rows
        ] == [
            (0, "Delta"),
            (1, "Echo"),
        ]

        document_path.write_text(
            "JARVIS persistence service integration. " * 200,
            encoding="utf-8",
        )

        add_document(
            database_path,
            object_uuid="document-001",
            object_path=document_path,
        )

        runner = AssimilationRunner(
            db,
            persistence_service=service,
        )

        result = runner.run_one_single_document(
            expected_object_uuid="document-001",
        )

        assert result["processed"] == 1, result
        assert result["failed"] == 0, result
        assert result["chunks"] > 0, result

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

            stored_chunks = conn.execute(
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
        assert stored_chunks == result["chunks"], (
            stored_chunks,
            result,
        )

    print("[PASS] Document text upsert")
    print("[PASS] Deterministic chunk persistence")
    print("[PASS] Existing chunks replaced atomically")
    print("[PASS] Persistence result metadata")
    print("[PASS] Runner delegates document persistence")
    print("[PASS] Document assimilation behavior preserved")


if __name__ == "__main__":
    main()

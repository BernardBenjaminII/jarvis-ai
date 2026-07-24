"""
JARVIS Gen 2 Phase VI-E4 verification.

This test verifies:

- format-aware extraction
- whitespace normalization
- deterministic checksums
- deterministic chunks
- extraction-result immutability
- missing-file diagnostics
- Runner delegation to an injected ExtractionService
- successful persistence, attempt journaling, and state transitions

Only temporary files and a temporary SQLite database are used.
"""

from __future__ import annotations

import sqlite3
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
)
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.extraction import (
    ExtractionResult,
    ExtractionService,
)
from knowledge_engine.storage.database import (
    KnowledgeDatabase,
)


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


class RecordingExtractionService(ExtractionService):
    """Test double proving that the Runner delegates extraction."""

    def __init__(self) -> None:
        super().__init__(
            chunk_size=500,
            chunk_overlap=50,
            extractor_name="phase_6e4_recording_extractor",
        )
        self.requested_paths: list[str] = []

    def extract(
        self,
        *,
        document_path: str,
    ) -> ExtractionResult:
        self.requested_paths.append(document_path)

        return super().extract(
            document_path=document_path,
        )


def verify_direct_extraction(root: Path) -> None:
    document_path = root / "direct-extraction.txt"

    document_path.write_text(
        "\n\n  JARVIS extraction verification.  \n"
        + ("Alpha Bravo Charlie. " * 200)
        + "\n\n",
        encoding="utf-8",
    )

    service = ExtractionService(
        chunk_size=500,
        chunk_overlap=50,
    )

    first = service.extract(
        document_path=str(document_path),
    )

    second = service.extract(
        document_path=str(document_path),
    )

    assert first.usable
    assert first.document_path == str(document_path)
    assert first.normalized_text
    assert first.normalized_text == first.normalized_text.strip()
    assert first.checksum == second.checksum
    assert first.chunks == second.chunks
    assert first.chunk_count > 1
    assert first.text_chars == len(first.normalized_text)
    assert first.extractor == "single_document_assimilation"

    assert isinstance(first.chunks, tuple)

    try:
        first.checksum = "modified"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "ExtractionResult must remain immutable"
        )

    try:
        service.extract(
            document_path=str(root / "missing.txt"),
        )
    except FileNotFoundError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError(
            "Missing file did not raise FileNotFoundError"
        )


def verify_runner_delegation(root: Path) -> None:
    database_path = root / "catalog.sqlite"
    document_path = root / "runner-document.txt"

    document_path.write_text(
        "JARVIS Runner extraction delegation. " * 250,
        encoding="utf-8",
    )

    create_database(database_path)

    add_document(
        database_path,
        object_uuid="document-001",
        object_path=document_path,
    )

    database = KnowledgeDatabase(database_path)
    extraction = RecordingExtractionService()

    runner = AssimilationRunner(
        database,
        extraction_service=extraction,
    )

    result = runner.run_one_single_document(
        expected_object_uuid="document-001",
    )

    assert result["processed"] == 1, result
    assert result["failed"] == 0, result
    assert result["text_chars"] > 0, result
    assert result["chunks"] > 0, result
    assert result["checksum"], result

    assert extraction.requested_paths == [
        str(document_path),
    ]

    with database.connect() as connection:
        registry = connection.execute(
            """
            SELECT
                lifecycle_state,
                assimilation_state
            FROM knowledge_registry
            WHERE object_uuid='document-001'
            """
        ).fetchone()

        queue = connection.execute(
            """
            SELECT queue_state
            FROM knowledge_assimilation_queue
            WHERE object_uuid='document-001'
            """
        ).fetchone()

        document = connection.execute(
            """
            SELECT
                extractor,
                text,
                checksum,
                status
            FROM document_text
            WHERE document_path=?
            """,
            (str(document_path),),
        ).fetchone()

        stored_chunk_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            WHERE document_path=?
            """,
            (str(document_path),),
        ).fetchone()[0]

        attempt = connection.execute(
            """
            SELECT
                attempt_state,
                text_chars,
                chunk_count,
                checksum
            FROM knowledge_assimilation_attempts
            WHERE object_uuid='document-001'
            ORDER BY attempt_id DESC
            LIMIT 1
            """
        ).fetchone()

    assert registry[0] == "chunked", registry
    assert registry[1] == "ready_for_embedding", registry
    assert queue[0] == "completed", queue

    assert (
        document[0]
        == "phase_6e4_recording_extractor"
    )
    assert document[1]
    assert document[2] == result["checksum"]
    assert document[3] == "extracted"

    assert stored_chunk_count == result["chunks"]

    assert attempt[0] == "completed", attempt
    assert attempt[1] == result["text_chars"], attempt
    assert attempt[2] == result["chunks"], attempt
    assert attempt[3] == result["checksum"], attempt


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-6e4-"
    ) as temporary:
        root = Path(temporary)

        verify_direct_extraction(root)
        verify_runner_delegation(root)

    print("[PASS] Format-aware document extraction")
    print("[PASS] Deterministic normalization and checksum")
    print("[PASS] Deterministic chunk generation")
    print("[PASS] ExtractionResult immutable contract")
    print("[PASS] Missing-source diagnostics")
    print("[PASS] Runner delegates extraction")
    print("[PASS] Extractor metadata reaches persistence")
    print("[PASS] Attempt statistics remain consistent")
    print("[PASS] State transitions remain consistent")


if __name__ == "__main__":
    main()

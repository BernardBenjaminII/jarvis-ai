"""
JARVIS Gen 2 Phase VI-F4.

Determinism and Performance Contracts.

All tests use temporary filesystem and SQLite fixtures. The live JARVIS
catalog is never opened.

The limits in this suite are deliberately generous. They are regression
guards, not competitive benchmarks.
"""

from __future__ import annotations

import gc
import json
import sqlite3
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any

from knowledge_engine.assimilation.collection_plan import (
    CollectionExpansionPlanner,
)
from knowledge_engine.assimilation.repositories import (
    KnowledgeRegistryRepository,
)
from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
)
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.extraction import (
    ExtractionService,
)
from knowledge_engine.storage.database import (
    KnowledgeDatabase,
)


# These are safety ceilings, not performance targets.
MAX_EXTRACTION_SECONDS = 10.0
MIN_EXTRACTION_MIB_PER_SECOND = 0.05

RUNNER_CONSTRUCTION_COUNT = 500
MAX_RUNNER_CONSTRUCTION_SECONDS = 5.0
MAX_RUNNER_CONSTRUCTION_PEAK_MIB = 32.0

REPOSITORY_LOOKUP_COUNT = 500
MAX_REPOSITORY_LOOKUP_SECONDS = 10.0

END_TO_END_DOCUMENT_COUNT = 12
MAX_END_TO_END_SECONDS = 20.0


def mib(value: int | float) -> float:
    return float(value) / (1024.0 * 1024.0)


def create_catalog(path: Path) -> None:
    """Create the smallest catalog supporting end-to-end assimilation."""

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


def register_document(
    database_path: Path,
    *,
    object_uuid: str,
    document_path: Path,
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
            str(document_path),
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


def create_registry_only_catalog(path: Path) -> None:
    connection = sqlite3.connect(path)

    connection.execute(
        """
        CREATE TABLE knowledge_registry (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            assimilation_state TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )

    connection.execute(
        """
        INSERT INTO knowledge_registry (
            object_uuid,
            object_path,
            object_type,
            lifecycle_state,
            assimilation_state,
            updated_at
        )
        VALUES (
            'collection-001',
            '/tmp/collection',
            'source_collection',
            'validated',
            'queued',
            '2026-07-13 12:00:00'
        )
        """
    )

    connection.commit()
    connection.close()


def verify_extraction_determinism(root: Path) -> dict[str, Any]:
    document = root / "deterministic-document.txt"

    payload = (
        "JARVIS deterministic extraction contract. "
        "Alpha Bravo Charlie Delta Echo.\n"
    ) * 30000

    document.write_text(
        payload,
        encoding="utf-8",
    )

    service = ExtractionService(
        chunk_size=2000,
        chunk_overlap=200,
    )

    before_state = dict(service.__dict__)

    started = time.perf_counter()

    results = [
        service.extract(
            document_path=str(document),
        )
        for _ in range(3)
    ]

    elapsed = time.perf_counter() - started

    first = results[0]

    for result in results[1:]:
        assert result.checksum == first.checksum
        assert result.chunks == first.chunks
        assert result.normalized_text == first.normalized_text
        assert result.chunk_count == first.chunk_count
        assert result.text_chars == first.text_chars

    assert service.__dict__ == before_state, (
        "ExtractionService accumulated hidden mutable state"
    )

    source_mib = mib(document.stat().st_size)
    throughput = (source_mib * len(results)) / max(elapsed, 0.000001)

    assert elapsed < MAX_EXTRACTION_SECONDS, {
        "elapsed_seconds": elapsed,
        "limit_seconds": MAX_EXTRACTION_SECONDS,
    }

    assert throughput >= MIN_EXTRACTION_MIB_PER_SECOND, {
        "throughput_mib_per_second": throughput,
        "minimum": MIN_EXTRACTION_MIB_PER_SECOND,
    }

    return {
        "source_mib": round(source_mib, 3),
        "runs": len(results),
        "elapsed_seconds": round(elapsed, 6),
        "throughput_mib_per_second": round(throughput, 3),
        "text_chars": first.text_chars,
        "chunk_count": first.chunk_count,
        "checksum": first.checksum,
    }


def verify_collection_plan_determinism(root: Path) -> dict[str, Any]:
    collection = root / "collection"
    collection.mkdir()

    (collection / "alpha.txt").write_text(
        "Alpha",
        encoding="utf-8",
    )
    (collection / "bravo.md").write_text(
        "# Bravo",
        encoding="utf-8",
    )
    (collection / "charlie.pdf").write_bytes(
        b"%PDF-1.4\n"
    )
    (collection / "delta.bin").write_bytes(
        b"\x00\x01\x02"
    )
    (collection / ".hidden.txt").write_text(
        "Hidden",
        encoding="utf-8",
    )

    nested = collection / "nested"
    nested.mkdir()

    planner = CollectionExpansionPlanner()

    plans = [
        planner.plan(
            object_uuid="collection-001",
            collection_path=str(collection),
        ).to_dict()
        for _ in range(5)
    ]

    canonical = json.dumps(
        plans[0],
        sort_keys=True,
        separators=(",", ":"),
    )

    for plan in plans[1:]:
        assert json.dumps(
            plan,
            sort_keys=True,
            separators=(",", ":"),
        ) == canonical

    return {
        "runs": len(plans),
        "serialized_plan_bytes": len(
            canonical.encode("utf-8")
        ),
    }


def verify_repository_determinism(root: Path) -> dict[str, Any]:
    database_path = root / "registry.sqlite"
    create_registry_only_catalog(database_path)

    repository = KnowledgeRegistryRepository(
        KnowledgeDatabase(database_path)
    )

    started = time.perf_counter()

    results = [
        repository.get_source_collection(
            object_uuid="collection-001",
        )
        for _ in range(REPOSITORY_LOOKUP_COUNT)
    ]

    elapsed = time.perf_counter() - started

    first = results[0]

    assert first is not None

    for result in results[1:]:
        assert result == first
        assert result is not first

    assert elapsed < MAX_REPOSITORY_LOOKUP_SECONDS, {
        "elapsed_seconds": elapsed,
        "limit_seconds": MAX_REPOSITORY_LOOKUP_SECONDS,
    }

    return {
        "lookups": REPOSITORY_LOOKUP_COUNT,
        "elapsed_seconds": round(elapsed, 6),
        "lookups_per_second": round(
            REPOSITORY_LOOKUP_COUNT
            / max(elapsed, 0.000001),
            2,
        ),
    }


def verify_runner_construction_contract() -> dict[str, Any]:
    database = KnowledgeDatabase(":memory:")

    gc.collect()
    tracemalloc.start()

    started = time.perf_counter()

    runners = [
        AssimilationRunner(database)
        for _ in range(RUNNER_CONSTRUCTION_COUNT)
    ]

    elapsed = time.perf_counter() - started
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert len(runners) == RUNNER_CONSTRUCTION_COUNT

    assert elapsed < MAX_RUNNER_CONSTRUCTION_SECONDS, {
        "elapsed_seconds": elapsed,
        "limit_seconds": MAX_RUNNER_CONSTRUCTION_SECONDS,
    }

    peak_mib = mib(peak_bytes)

    assert peak_mib < MAX_RUNNER_CONSTRUCTION_PEAK_MIB, {
        "peak_mib": peak_mib,
        "limit_mib": MAX_RUNNER_CONSTRUCTION_PEAK_MIB,
    }

    first = runners[0]
    second = runners[1]

    assert first.state_service is not second.state_service
    assert (
        first.persistence_service
        is not second.persistence_service
    )
    assert first.attempt_service is not second.attempt_service
    assert (
        first.extraction_service
        is not second.extraction_service
    )

    del runners
    gc.collect()

    return {
        "runner_count": RUNNER_CONSTRUCTION_COUNT,
        "elapsed_seconds": round(elapsed, 6),
        "constructions_per_second": round(
            RUNNER_CONSTRUCTION_COUNT
            / max(elapsed, 0.000001),
            2,
        ),
        "current_memory_mib": round(
            mib(current_bytes),
            3,
        ),
        "peak_memory_mib": round(
            peak_mib,
            3,
        ),
    }


def verify_end_to_end_baseline(root: Path) -> dict[str, Any]:
    database_path = root / "assimilation.sqlite"
    create_catalog(database_path)

    for index in range(END_TO_END_DOCUMENT_COUNT):
        document_path = root / f"document-{index:03d}.txt"

        document_path.write_text(
            (
                f"JARVIS end-to-end baseline document {index}. "
                "Deterministic bounded assimilation.\n"
            )
            * 500,
            encoding="utf-8",
        )

        register_document(
            database_path,
            object_uuid=f"document-{index:03d}",
            document_path=document_path,
        )

    database = KnowledgeDatabase(database_path)
    runner = AssimilationRunner(database)

    started = time.perf_counter()

    results = [
        runner.run_one_single_document(
            expected_object_uuid=f"document-{index:03d}",
        )
        for index in range(END_TO_END_DOCUMENT_COUNT)
    ]

    elapsed = time.perf_counter() - started

    assert all(
        result["processed"] == 1
        and result["failed"] == 0
        for result in results
    ), results

    assert elapsed < MAX_END_TO_END_SECONDS, {
        "elapsed_seconds": elapsed,
        "limit_seconds": MAX_END_TO_END_SECONDS,
    }

    with database.connect() as connection:
        completed_queue = connection.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_assimilation_queue
            WHERE queue_state='completed'
            """
        ).fetchone()[0]

        completed_attempts = connection.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_assimilation_attempts
            WHERE attempt_state='completed'
            """
        ).fetchone()[0]

        ready_objects = connection.execute(
            """
            SELECT COUNT(*)
            FROM knowledge_registry
            WHERE lifecycle_state='chunked'
              AND assimilation_state='ready_for_embedding'
            """
        ).fetchone()[0]

        document_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM document_text
            WHERE status='extracted'
            """
        ).fetchone()[0]

        total_chunks = connection.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            """
        ).fetchone()[0]

    assert completed_queue == END_TO_END_DOCUMENT_COUNT
    assert completed_attempts == END_TO_END_DOCUMENT_COUNT
    assert ready_objects == END_TO_END_DOCUMENT_COUNT
    assert document_rows == END_TO_END_DOCUMENT_COUNT
    assert total_chunks > 0

    return {
        "documents": END_TO_END_DOCUMENT_COUNT,
        "elapsed_seconds": round(elapsed, 6),
        "documents_per_second": round(
            END_TO_END_DOCUMENT_COUNT
            / max(elapsed, 0.000001),
            2,
        ),
        "total_chunks": total_chunks,
        "average_chunks_per_document": round(
            total_chunks / END_TO_END_DOCUMENT_COUNT,
            2,
        ),
    }


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-6f4-"
    ) as temporary:
        root = Path(temporary)

        metrics = {
            "extraction": verify_extraction_determinism(root),
            "collection_planning": (
                verify_collection_plan_determinism(root)
            ),
            "repository": verify_repository_determinism(root),
            "runner_construction": (
                verify_runner_construction_contract()
            ),
            "end_to_end": verify_end_to_end_baseline(root),
        }

    print("[PASS] Extraction output is deterministic")
    print("[PASS] ExtractionService remains stateless")
    print("[PASS] Extraction throughput remains bounded")
    print("[PASS] Collection planning is deterministic")
    print("[PASS] Repository reads are deterministic")
    print("[PASS] Repository lookup cost remains bounded")
    print("[PASS] Runner construction remains lightweight")
    print("[PASS] Runner default services remain instance-scoped")
    print("[PASS] End-to-end assimilation remains bounded")
    print("[PASS] End-to-end state remains internally consistent")

    print("----------------------------------------------------------------------")
    print("PERFORMANCE BASELINE")
    print("----------------------------------------------------------------------")
    print(
        json.dumps(
            metrics,
            indent=2,
            sort_keys=True,
        )
    )
    print("----------------------------------------------------------------------")
    print("[PASS] All determinism and performance contracts verified")


if __name__ == "__main__":
    main()

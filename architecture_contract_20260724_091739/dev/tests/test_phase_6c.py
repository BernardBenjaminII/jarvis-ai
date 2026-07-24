"""
Regression verification for JARVIS Gen 2 Phase VI-C.

Uses a temporary catalog only.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation import (
    AssimilationDirector,
    AssimilationRunner,
    MissionStatus,
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
    timestamp: str,
) -> None:
    connection = sqlite3.connect(database_path)

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
            ?, ?, 'single_document',
            'validated', 'queued', ?
        )
        """,
        (
            object_uuid,
            str(object_path),
            timestamp,
        ),
    )

    connection.execute(
        """
        INSERT INTO knowledge_assimilation_queue (
            object_uuid,
            queue_state,
            updated_at
        )
        VALUES (?, 'queued', ?)
        """,
        (
            object_uuid,
            timestamp,
        ),
    )

    connection.commit()
    connection.close()


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-6c-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"

        create_test_database(database_path)

        for index in range(1, 4):
            document = root / f"document-{index}.txt"
            document.write_text(
                (
                    f"Persistent mission recovery document {index}. "
                    * 200
                ),
                encoding="utf-8",
            )

            add_document(
                database_path,
                object_uuid=f"document-{index}",
                object_path=document,
                timestamp=f"2026-01-01 00:0{index}:00",
            )

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
            limit=3,
            object_types=["single_document"],
            persist=True,
        )

        assert mission.total_items == 3
        assert mission.status == MissionStatus.PLANNED

        stored = director.load_mission(mission.mission_id)

        assert stored.mission_id == mission.mission_id
        assert stored.total_items == 3

        paused = director.execute(
            mission,
            max_items=1,
        )

        assert paused.status == MissionStatus.PAUSED
        assert paused.processed == 1
        assert paused.remaining_items == 2

        reloaded = director.load_mission(mission.mission_id)

        assert reloaded.status == MissionStatus.PAUSED
        assert reloaded.processed == 1
        assert reloaded.remaining_items == 2

        item_rows = director.mission_store.mission_items(
            mission.mission_id
        )

        assert len(item_rows) == 3
        assert item_rows[0]["status"] == "completed"
        assert item_rows[1]["status"] == "queued"
        assert item_rows[2]["status"] == "queued"

        paused_again = director.resume(
            mission.mission_id,
            max_items=1,
            recover_stale_minutes=30,
        )

        assert paused_again.status == MissionStatus.PAUSED
        assert paused_again.processed == 2
        assert paused_again.remaining_items == 1

        completed = director.resume(
            mission.mission_id,
            max_items=5,
            recover_stale_minutes=30,
        )

        assert completed.status == MissionStatus.COMPLETED
        assert completed.processed == 3
        assert completed.remaining_items == 0

        final = director.load_mission(mission.mission_id)

        assert final.status == MissionStatus.COMPLETED
        assert final.processed == 3

        history = director.history(limit=10)

        assert any(
            row["mission_id"] == mission.mission_id
            and row["status"] == "completed"
            for row in history
        )

        with db.connect() as connection:
            completed_documents = connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_registry
                WHERE lifecycle_state='chunked'
                  AND assimilation_state='ready_for_embedding'
                """
            ).fetchone()[0]

            mission_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_assimilation_missions
                """
            ).fetchone()[0]

            mission_item_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_assimilation_mission_items
                """
            ).fetchone()[0]

        assert completed_documents == 3
        assert mission_count == 1
        assert mission_item_count == 3

    print("[PASS] Persistent mission creation")
    print("[PASS] Mission reconstruction")
    print("[PASS] Per-item durable checkpointing")
    print("[PASS] Bounded execution pause")
    print("[PASS] Resume from persistent mission ID")
    print("[PASS] Multiple pause/resume cycles")
    print("[PASS] Mission completion")
    print("[PASS] Mission history")
    print("[PASS] No duplicate document processing")


if __name__ == "__main__":
    main()

"""
Regression verification for Phase VI-D2 collection expansion planning.

Uses only temporary directories and a temporary SQLite catalog.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from knowledge_engine.assimilation.collection_plan import (
    CollectionExpansionPlanner,
)
from knowledge_engine.assimilation.handlers.source_collection import (
    SourceCollectionHandler,
)
from knowledge_engine.assimilation.registry_builder import (
    build_handler_registry,
)
from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.storage.database import KnowledgeDatabase


def create_test_database(path: Path) -> None:
    connection = sqlite3.connect(path)

    connection.execute(
        """
        CREATE TABLE knowledge_registry (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            assimilation_state TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def register_collection(
    database_path: Path,
    *,
    object_uuid: str,
    collection_path: Path,
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
        VALUES (
            ?, ?, 'source_collection', 'validated', 'queued'
        )
        """,
        (
            object_uuid,
            str(collection_path),
        ),
    )

    connection.commit()
    connection.close()


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-6d2-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"
        collection = root / "source_collection"

        collection.mkdir()

        (collection / "Alpha.pdf").write_bytes(b"%PDF-test")
        (collection / "bravo.md").write_text(
            "# Bravo",
            encoding="utf-8",
        )
        (collection / "charlie.png").write_bytes(b"PNG-test")
        (collection / "delta.bin").write_bytes(b"binary-test")
        (collection / "EchoFolder").mkdir()
        (collection / ".hidden.txt").write_text(
            "hidden",
            encoding="utf-8",
        )

        create_test_database(database_path)

        register_collection(
            database_path,
            object_uuid="collection-001",
            collection_path=collection,
        )

        db = KnowledgeDatabase(database_path)
        runner = AssimilationRunner(db)
        registry = build_handler_registry(runner)

        assert registry.supports("single_document")
        assert registry.supports("source_collection")

        handler = registry.get("source_collection")

        assert isinstance(handler, SourceCollectionHandler)

        result = handler.execute(
            object_uuid="collection-001",
        )

        assert result["failed"] == 0, result
        assert result["status"] == "planned", result
        assert result["processed"] == 0, result

        plan = result["plan"]
        summary = plan["summary"]
        children = plan["children"]

        assert summary["total_children"] == 5, summary
        assert summary["skipped_entries"] == 1, summary

        assert [
            child["name"]
            for child in children
        ] == [
            "Alpha.pdf",
            "bravo.md",
            "charlie.png",
            "delta.bin",
            "EchoFolder",
        ]

        types_by_name = {
            child["name"]: child["object_type"]
            for child in children
        }

        assert types_by_name["Alpha.pdf"] == "single_document"
        assert types_by_name["bravo.md"] == "single_document"
        assert types_by_name["charlie.png"] == "single_image"
        assert types_by_name["delta.bin"] == "single_file"
        assert types_by_name["EchoFolder"] == "folder_collection"

        planner = CollectionExpansionPlanner()

        first_plan = planner.plan(
            object_uuid="collection-001",
            collection_path=collection,
        )

        second_plan = planner.plan(
            object_uuid="collection-001",
            collection_path=collection,
        )

        assert first_plan.fingerprint == second_plan.fingerprint

        missing = handler.execute(
            object_uuid="does-not-exist",
        )

        assert missing["failed"] == 1
        assert missing["status"] == "not_found"

        with db.connect() as connection:
            registry_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_registry
                """
            ).fetchone()[0]

        assert registry_count == 1

    print("[PASS] Source collection registry resolution")
    print("[PASS] Deterministic direct-child ordering")
    print("[PASS] Document child classification")
    print("[PASS] Image child classification")
    print("[PASS] Generic-file classification")
    print("[PASS] Nested-folder recognition")
    print("[PASS] Hidden-entry exclusion")
    print("[PASS] Stable collection-plan fingerprint")
    print("[PASS] Missing collection handling")
    print("[PASS] No registry writes during planning")


if __name__ == "__main__":
    main()

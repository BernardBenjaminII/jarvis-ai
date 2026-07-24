from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.integration.bootstrap import build_default_integration_runtime
from core.integration.knowledge_inventory import (
    KnowledgeInventoryConfig,
    KnowledgeInventoryService,
)
from core.integration.providers.knowledge import KnowledgeProjectionProvider


class FakeValue:
    def to_dict(self):
        return {"state": "healthy"}


class FakeEventRegistry:
    def list_events(self, limit=100):
        return []


class FakeOperationsService:
    def __init__(self):
        self.event_registry = FakeEventRegistry()

    def snapshot(self):
        return FakeValue()

    def executive(self):
        return FakeValue()

    def health(self):
        return FakeValue()

    def missions(self):
        return []

    def resources(self):
        return FakeValue()

    def timeline(self, limit=100):
        return FakeValue()


class KnowledgeInventoryProjectionTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        (root / "documents").mkdir()
        (root / "documents" / "alpha.txt").write_text(
            "alpha",
            encoding="utf-8",
        )
        (root / "documents" / "beta.md").write_text(
            "beta",
            encoding="utf-8",
        )

        database = root / "catalog.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute(
                "CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT)"
            )
            connection.executemany(
                "INSERT INTO documents(title) VALUES (?)",
                [("One",), ("Two",), ("Three",)],
            )
            connection.commit()

    def test_inventory_reads_files_and_database_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)

            service = KnowledgeInventoryService(
                KnowledgeInventoryConfig(
                    root=root,
                    ttl_seconds=0,
                    max_files=100,
                )
            )
            inventory = service.inventory()

            self.assertTrue(inventory["root_exists"])
            self.assertEqual(inventory["database_count"], 1)
            self.assertEqual(inventory["database_total_rows"], 3)
            self.assertGreaterEqual(
                inventory["filesystem"]["total_files"],
                3,
            )
            self.assertIsNotNone(inventory["fingerprint"])

    def test_missing_root_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            service = KnowledgeInventoryService(
                KnowledgeInventoryConfig(
                    root=missing,
                    ttl_seconds=0,
                    max_files=100,
                )
            )
            projection = KnowledgeProjectionProvider(
                service
            ).project().to_dict()

            self.assertEqual(
                projection["health"]["status"],
                "not_configured",
            )

    def test_available_projection_has_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)

            service = KnowledgeInventoryService(
                KnowledgeInventoryConfig(
                    root=root,
                    ttl_seconds=0,
                    max_files=100,
                )
            )
            projection = KnowledgeProjectionProvider(
                service
            ).project().to_dict()

            self.assertEqual(
                projection["health"]["status"],
                "available",
            )
            self.assertEqual(
                projection["data"]["summary"]["database_count"],
                1,
            )
            self.assertEqual(
                projection["data"]["summary"]["database_total_rows"],
                3,
            )

    def test_inventory_cache_can_be_invalidated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)

            service = KnowledgeInventoryService(
                KnowledgeInventoryConfig(
                    root=root,
                    ttl_seconds=3600,
                    max_files=100,
                )
            )
            first = service.inventory()

            (root / "new.txt").write_text(
                "new",
                encoding="utf-8",
            )

            cached = service.inventory()
            self.assertEqual(
                cached["filesystem"]["total_files"],
                first["filesystem"]["total_files"],
            )

            service.invalidate()
            refreshed = service.inventory()
            self.assertGreater(
                refreshed["filesystem"]["total_files"],
                first["filesystem"]["total_files"],
            )

    def test_bootstrap_registers_knowledge_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)

            service = KnowledgeInventoryService(
                KnowledgeInventoryConfig(
                    root=root,
                    ttl_seconds=0,
                    max_files=100,
                )
            )
            runtime = build_default_integration_runtime(
                operations_service=FakeOperationsService(),
                capability_packages=[],
                knowledge_inventory_service=service,
            )

            self.assertIn(
                "knowledge",
                runtime.projection_registry,
            )
            projection = runtime.projection_service.projection(
                "knowledge"
            ).to_dict()
            self.assertEqual(
                projection["projection_id"],
                "knowledge",
            )


if __name__ == "__main__":
    unittest.main()

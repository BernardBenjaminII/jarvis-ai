"""C-4A Knowledge Catalog compatibility repair certification."""
from __future__ import annotations

from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from core.knowledge_catalog import database
from core.knowledge_catalog.search import search_catalog


class KnowledgeCompatibilityRepairTests(unittest.TestCase):
    def test_migrate_does_not_require_structure_sql_export(self) -> None:
        with TemporaryDirectory() as temp:
            db_path = Path(temp) / "catalog.sqlite"
            self.assertFalse(hasattr(database.catalog_schema, "STRUCTURE_SQL"))
            database.migrate(db_path)

            with sqlite3.connect(db_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            self.assertIn("documents", tables)
            self.assertIn("catalog_documents", tables)
            self.assertIn("document_subjects", tables)

    def test_migrate_remains_idempotent(self) -> None:
        with TemporaryDirectory() as temp:
            db_path = Path(temp) / "catalog.sqlite"
            database.migrate(db_path)
            database.migrate(db_path)

    def test_search_catalog_operates_after_compatibility_migration(self) -> None:
        with TemporaryDirectory() as temp:
            db_path = Path(temp) / "catalog.sqlite"
            database.migrate(db_path)
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO document_subjects(
                        file_path, sha256, subject, confidence, assigned_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "/knowledge/linux/guide.pdf",
                        "abc123",
                        "Linux administration",
                        0.92,
                        "test",
                        "2026-07-24T00:00:00Z",
                    ),
                )
            rows = search_catalog("Linux", db_path=db_path, limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["subject"], "Linux administration")


if __name__ == "__main__":
    unittest.main()

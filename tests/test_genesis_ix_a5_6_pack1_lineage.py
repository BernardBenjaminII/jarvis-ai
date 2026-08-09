from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dev.metadata_lineage.audit import MetadataJoinLineageAudit
from dev.metadata_lineage.join_analysis import normalize_name


class GenesisIXA56Pack1Tests(unittest.TestCase):
    def make_database(self, root: Path) -> Path:
        path = root / "catalog.sqlite"
        connection = sqlite3.connect(path)
        connection.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                path TEXT,
                category TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY,
                document_path TEXT,
                text TEXT
            )
            """
        )
        connection.executemany(
            "INSERT INTO documents(path, category) VALUES (?, ?)",
            [
                ("/tmp/a.md", "programming"),
                ("/tmp/b.md", "medical"),
            ],
        )
        connection.executemany(
            "INSERT INTO chunks(document_path, text) VALUES (?, ?)",
            [
                ("/tmp/a.md", "a"),
                ("/tmp/a.md", "b"),
                ("/tmp/b.md", "c"),
            ],
        )
        connection.commit()
        connection.close()
        return path

    def test_key_normalization(self):
        self.assertEqual(normalize_name("document_path"), "path")
        self.assertEqual(normalize_name("source_id"), "id")

    def test_lineage_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_database(root)

            report = MetadataJoinLineageAudit(
                project_root=root,
                knowledge_root=root,
            ).execute()

            self.assertGreater(
                report.summary["join_candidate_count"],
                0,
            )
            self.assertGreater(
                report.summary["metadata_lineage_count"],
                0,
            )

    def test_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.make_database(root)
            before = path.read_bytes()

            MetadataJoinLineageAudit(
                project_root=root,
                knowledge_root=root,
            ).execute()

            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest

from dev.audits.audit_genesis_ix_a4_retrieval_architecture import (
    database_inventory,
    routes,
    symbols,
)

class GenesisIXA4AuditTests(unittest.TestCase):
    def test_symbol_census(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core" / "retrieval.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "class CatalogGroundingService:\n"
                "    def search_catalog(self):\n"
                "        pass\n",
                encoding="utf-8",
            )
            names = {item.name for item in symbols(root)}
            self.assertIn("CatalogGroundingService", names)
            self.assertIn("search_catalog", names)

    def test_route_census(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/src/routes/knowledge.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                '@router.post("/api/knowledge/conversation")\n'
                "def knowledge_conversation():\n"
                "    pass\n",
                encoding="utf-8",
            )
            found = routes(root)
            self.assertEqual(found[0].method, "POST")
            self.assertEqual(found[0].route, "/api/knowledge/conversation")

    def test_database_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "catalog.sqlite"
            with sqlite3.connect(db) as conn:
                conn.execute(
                    "CREATE TABLE runtime_chunks "
                    "(id INTEGER PRIMARY KEY, chunk_text TEXT)"
                )
                conn.execute(
                    "INSERT INTO runtime_chunks(chunk_text) VALUES ('evidence')"
                )
            inventory = database_inventory(db)
            table = next(
                item for item in inventory["tables"]
                if item["name"] == "runtime_chunks"
            )
            self.assertEqual(table["row_count"], 1)

if __name__ == "__main__":
    unittest.main()

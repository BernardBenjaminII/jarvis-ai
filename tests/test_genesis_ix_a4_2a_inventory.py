from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest

from core.retrieval.inspection import inspect_components, inspect_tables
from core.retrieval.inventory import build_inventory

class GenesisIXA42ATests(unittest.TestCase):
    def test_discovers_search_function(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/search.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "def search_catalog(conn, query):\n"
                "    return conn.execute('SELECT * FROM runtime_chunks WHERE chunk_text LIKE ?', (query,))\n",
                encoding="utf-8",
            )
            self.assertTrue(any(x["name"] == "search_catalog" for x in inspect_components(root)))

    def test_excludes_snapshot_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "core/search.py"
            old = root / "genesis_old/core/search.py"
            live.parent.mkdir(parents=True)
            old.parent.mkdir(parents=True)
            live.write_text("def search_catalog():\n    pass\n", encoding="utf-8")
            old.write_text("def search_catalog():\n    pass\n", encoding="utf-8")
            paths = {x["path"] for x in inspect_components(root)}
            self.assertIn("core/search.py", paths)
            self.assertNotIn("genesis_old/core/search.py", paths)

    def test_table_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "core/search.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "def search_catalog(conn):\n"
                "    return conn.execute('SELECT * FROM runtime_chunks')\n",
                encoding="utf-8",
            )
            db = root / "catalog.sqlite"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE runtime_chunks (id INTEGER PRIMARY KEY, chunk_text TEXT)")
                conn.execute("INSERT INTO runtime_chunks(chunk_text) VALUES ('x')")
            table = next(x for x in inspect_tables(db, inspect_components(root))
                         if x["name"] == "runtime_chunks")
            self.assertEqual(table["row_count"], 1)
            self.assertEqual(table["classification"], "READ_ONLY")

    def test_inventory_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/search.py"
            path.parent.mkdir(parents=True)
            path.write_text("def search_catalog():\n    return []\n", encoding="utf-8")
            data = build_inventory(root, None)
            self.assertGreaterEqual(data["summary"]["component_count"], 1)

if __name__ == "__main__":
    unittest.main()

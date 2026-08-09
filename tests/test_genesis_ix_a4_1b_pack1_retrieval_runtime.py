from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest

from dev.audits.audit_genesis_ix_a4_1b_pack1_retrieval_runtime import (
    database_inventory,
    function_inventory,
    table_ownership,
)


class GenesisIXA41BPack1Tests(unittest.TestCase):
    def test_function_inventory_finds_search_and_sql(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/search.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "def search_catalog(conn, query):\n"
                "    return conn.execute("
                "'SELECT * FROM runtime_chunks WHERE chunk_text LIKE ?', "
                "(query,))\n",
                encoding="utf-8",
            )

            functions, _, _ = function_inventory(root)

            self.assertEqual(len(functions), 1)
            self.assertIn("runtime_chunks", functions[0].sql_reads)

    def test_excludes_historical_snapshot_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            canonical = root / "core/search.py"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                "def search_catalog():\n    pass\n",
                encoding="utf-8",
            )

            snapshot = root / "genesis_iv_a9/core/search.py"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text(
                "def search_catalog():\n    pass\n",
                encoding="utf-8",
            )

            functions, _, _ = function_inventory(root)

            self.assertEqual(
                [item.path for item in functions],
                ["core/search.py"],
            )

    def test_database_inventory_counts_tables(self) -> None:
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

            report = database_inventory(db)
            table = next(
                item for item in report["tables"]
                if item["name"] == "runtime_chunks"
            )

            self.assertEqual(table["row_count"], 1)

    def test_table_ownership_maps_readers_and_writers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/search.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "def search_catalog(conn):\n"
                "    conn.execute('SELECT * FROM runtime_chunks')\n"
                "    conn.execute("
                "'INSERT INTO chunk_embeddings(id) VALUES (1)')\n",
                encoding="utf-8",
            )

            functions, _, _ = function_inventory(root)
            ownership = table_ownership(
                functions,
                {
                    "tables": [
                        {"name": "runtime_chunks"},
                        {"name": "chunk_embeddings"},
                    ]
                },
            )

            self.assertTrue(ownership["runtime_chunks"]["readers"])
            self.assertTrue(ownership["chunk_embeddings"]["writers"])


if __name__ == "__main__":
    unittest.main()

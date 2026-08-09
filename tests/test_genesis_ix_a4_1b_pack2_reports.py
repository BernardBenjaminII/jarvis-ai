from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from dev.audits.generate_genesis_ix_a4_1b_pack2_reports import (
    canonical_decisions,
    duplicate_candidates,
    embedding_coverage,
    load_inventory,
)


class GenesisIXA41BPack2Tests(unittest.TestCase):
    def fixture(self) -> dict:
        return {
            "schema_version": "genesis_ix_a4_1b_pack1_v1",
            "classified_functions": [
                {
                    "module": "core.knowledge_catalog.search",
                    "qualified_name": "search_catalog",
                    "path": "core/knowledge_catalog/search.py",
                    "line": 8,
                    "parameters": ["query"],
                    "returns": "list[dict]",
                    "terms": ["search", "catalog"],
                    "runtime_status": "CANONICAL",
                },
                {
                    "module": "knowledge_engine.search.service",
                    "qualified_name": "search_catalog",
                    "path": "knowledge_engine/search/service.py",
                    "line": 30,
                    "parameters": ["query"],
                    "returns": "list[dict]",
                    "terms": ["search", "catalog"],
                    "runtime_status": "DORMANT",
                },
            ],
            "database": {
                "tables": [
                    {"name": "runtime_chunks", "row_count": 100},
                    {"name": "chunk_embeddings", "row_count": 25},
                ]
            },
            "runtime": {"objects": [], "search_functions": []},
            "table_ownership": {},
        }

    def test_load_inventory_validates_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(
                json.dumps(self.fixture()),
                encoding="utf-8",
            )
            loaded = load_inventory(path)
            self.assertEqual(
                loaded["schema_version"],
                "genesis_ix_a4_1b_pack1_v1",
            )

    def test_duplicate_detection_uses_production_modules(self) -> None:
        found = duplicate_candidates(
            self.fixture()["classified_functions"]
        )
        self.assertEqual(len(found), 1)
        self.assertIn("single canonical", found[0].recommendation)

    def test_canonical_decision_keeps_live_function(self) -> None:
        decisions = canonical_decisions(
            self.fixture()["classified_functions"]
        )
        canonical = next(
            item for item in decisions
            if item.component == "search_catalog"
            and item.module == "core.knowledge_catalog.search"
        )
        self.assertEqual(canonical.decision, "KEEP")

    def test_embedding_coverage(self) -> None:
        coverage = embedding_coverage(self.fixture())
        self.assertEqual(coverage["primary_chunk_count"], 100)
        self.assertEqual(coverage["primary_embedding_count"], 25)
        self.assertEqual(coverage["coverage_percent"], 25.0)
        self.assertEqual(coverage["status"], "partial")


if __name__ == "__main__":
    unittest.main()

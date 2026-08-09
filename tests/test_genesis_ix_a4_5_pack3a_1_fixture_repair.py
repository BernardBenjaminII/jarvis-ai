from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from core.retrieval.certification.semantic_fixture import (
    METADATA_TERMS,
    _clean_phrase,
    _meaningful,
    install_semantic_fixture_override,
    select_semantic_fixture,
)


class FakeTracer:
    def _select_known_query(self):
        return "sha256"


class GenesisIXA45Pack3A1Tests(unittest.TestCase):
    def test_metadata_term_is_not_meaningful(self) -> None:
        self.assertFalse(_meaningful("sha256"))
        self.assertFalse(_meaningful("file path confidence"))

    def test_semantic_phrase_is_meaningful(self) -> None:
        self.assertTrue(
            _meaningful("UH Black Hawk Hydraulic Maintenance")
        )

    def test_hashes_are_removed(self) -> None:
        value = _clean_phrase(
            "sha256 aabbccddeeff00112233445566778899 "
            "Hydraulic Maintenance Manual"
        )
        self.assertNotIn("sha256", value.casefold())
        self.assertIn("Hydraulic Maintenance Manual", value)

    def test_live_fixture_selection_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "catalog.sqlite"

            with sqlite3.connect(database) as conn:
                conn.executescript(
                    """
                    CREATE TABLE runtime_documents (
                        document_id INTEGER PRIMARY KEY,
                        title TEXT
                    );
                    CREATE TABLE runtime_chunks (
                        chunk_id INTEGER PRIMARY KEY,
                        chunk_text TEXT
                    );
                    INSERT INTO runtime_documents(title)
                    VALUES ('UH Black Hawk Hydraulic Maintenance Manual');
                    """
                )

            with patch(
                "core.retrieval.certification.semantic_fixture."
                "search_qualified_catalog",
                return_value=[{"file_path": "/knowledge/uh60.txt"}],
            ):
                result = select_semantic_fixture(database)

            self.assertIn("Hydraulic Maintenance", result.query)
            self.assertEqual(result.accepted_rows, 1)

    def test_runtime_selector_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "catalog.sqlite"

            with sqlite3.connect(database) as conn:
                conn.executescript(
                    """
                    CREATE TABLE runtime_documents (
                        document_id INTEGER PRIMARY KEY,
                        title TEXT
                    );
                    CREATE TABLE runtime_chunks (
                        chunk_id INTEGER PRIMARY KEY,
                        chunk_text TEXT
                    );
                    INSERT INTO runtime_documents(title)
                    VALUES ('SQLite Full Text Search Architecture');
                    """
                )

            tracer = FakeTracer()

            with patch(
                "core.retrieval.certification.semantic_fixture."
                "search_qualified_catalog",
                return_value=[{"file_path": "/knowledge/sqlite.txt"}],
            ):
                selection = install_semantic_fixture_override(
                    tracer,
                    database,
                )

            self.assertEqual(
                tracer._select_known_query(),
                selection.query,
            )
            self.assertEqual(
                selection.selector_method,
                "_select_known_query",
            )


if __name__ == "__main__":
    unittest.main()

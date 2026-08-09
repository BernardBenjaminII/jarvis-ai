from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
import unittest

from core.retrieval.certification.tracer import (
    EndToEndRetrievalTracer,
    check,
    mapping,
)


class GenesisIXA43Tests(unittest.TestCase):
    def test_check_passes(self) -> None:
        result = check(
            "TEST",
            "Test",
            True,
            "Expected true.",
        )
        self.assertTrue(result.passed)

    def test_check_fails(self) -> None:
        result = check(
            "TEST",
            "Test",
            False,
            "Expected false.",
        )
        self.assertFalse(result.passed)

    def test_mapping_uses_to_dict(self) -> None:
        class Value:
            def to_dict(self):
                return {"answer": "ok"}

        self.assertEqual(mapping(Value()), {"answer": "ok"})

    def test_database_terms(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "catalog.sqlite"

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE runtime_chunks "
                    "(id INTEGER PRIMARY KEY, chunk_text TEXT)"
                )
                connection.execute(
                    "INSERT INTO runtime_chunks(chunk_text) "
                    "VALUES ('Python retrieval architecture')"
                )

            tracer = EndToEndRetrievalTracer(
                repository_root=root,
                catalog_database=database,
            )
            terms = tracer._database_terms()

            self.assertIn("Python", terms)

    def test_json_safe(self) -> None:
        value = EndToEndRetrievalTracer._json_safe(
            {"items": (1, 2, 3)}
        )
        self.assertEqual(value, {"items": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()

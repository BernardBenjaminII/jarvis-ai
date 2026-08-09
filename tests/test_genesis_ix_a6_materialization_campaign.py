from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.knowledge_catalog.materialization_campaign.candidates import (
    discover_candidates,
)
from core.knowledge_catalog.materialization_campaign.checkpoint import (
    CheckpointStore,
)
from core.knowledge_catalog.materialization_campaign.contracts import (
    Candidate,
    CandidateDisposition,
    CandidateResult,
)


class GenesisIXA6Tests(unittest.TestCase):
    def create_catalogs(
        self,
        root: Path,
    ) -> tuple[Path, Path, Path]:
        knowledge = root / "Knowledge"
        knowledge.mkdir()
        file_a = knowledge / "a.txt"
        file_b = knowledge / "b.md"
        file_a.write_text(
            "alpha",
            encoding="utf-8",
        )
        file_b.write_text(
            "beta",
            encoding="utf-8",
        )

        runtime = root / "runtime.sqlite"
        connection = sqlite3.connect(runtime)
        connection.execute(
            """
            CREATE TABLE knowledge_classifications(
                id INTEGER PRIMARY KEY,
                file_path TEXT,
                category TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE runtime_documents(
                id INTEGER PRIMARY KEY,
                file_path TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO knowledge_classifications(
                file_path,
                category
            )
            VALUES(?, ?)
            """,
            (
                (str(file_a), "programming"),
                (str(file_b), "reference"),
            ),
        )
        connection.execute(
            """
            INSERT INTO runtime_documents(file_path)
            VALUES(?)
            """,
            (str(file_a),),
        )
        connection.commit()
        connection.close()

        inventory = root / "inventory.sqlite"
        connection = sqlite3.connect(inventory)
        connection.execute(
            """
            CREATE TABLE documents(
                id INTEGER PRIMARY KEY,
                path TEXT
            )
            """
        )
        connection.commit()
        connection.close()

        return (
            knowledge,
            runtime,
            inventory,
        )

    def test_candidate_discovery_excludes_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge, runtime, inventory = (
                self.create_catalogs(root)
            )
            candidates = discover_candidates(
                runtime_catalog=runtime,
                inventory_catalog=inventory,
                knowledge_root=knowledge,
            )
            self.assertEqual(
                len(candidates),
                1,
            )
            self.assertTrue(
                candidates[0].path.endswith("b.md")
            )

    def test_checkpoint_is_resumable(self):
        with tempfile.TemporaryDirectory() as temp:
            store = CheckpointStore(
                Path(temp) / "checkpoint.sqlite"
            )
            candidate = Candidate(
                candidate_id="id:1",
                path="/tmp/a.txt",
                extension=".txt",
            )
            self.assertEqual(
                store.register_candidates((candidate,)),
                1,
            )
            self.assertEqual(
                store.register_candidates((candidate,)),
                0,
            )
            self.assertEqual(
                len(
                    store.next_candidates(
                        limit=10,
                        retry_failures=False,
                    )
                ),
                1,
            )

    def test_checkpoint_records_result(self):
        with tempfile.TemporaryDirectory() as temp:
            store = CheckpointStore(
                Path(temp) / "checkpoint.sqlite"
            )
            candidate = Candidate(
                candidate_id="id:1",
                path="/tmp/a.txt",
                extension=".txt",
            )
            store.register_candidates((candidate,))
            store.record_result(
                CandidateResult(
                    candidate_id="id:1",
                    path="/tmp/a.txt",
                    disposition=(
                        CandidateDisposition.MATERIALIZED
                    ),
                    detail="done",
                )
            )
            self.assertEqual(
                store.disposition_counts()[
                    "MATERIALIZED"
                ],
                1,
            )

    def test_checkpoint_database_is_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge, runtime, inventory = (
                self.create_catalogs(root)
            )
            before = runtime.read_bytes()
            store = CheckpointStore(
                root / "checkpoint.sqlite"
            )
            candidates = discover_candidates(
                runtime_catalog=runtime,
                inventory_catalog=inventory,
                knowledge_root=knowledge,
            )
            store.register_candidates(candidates)
            self.assertEqual(
                before,
                runtime.read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from dev.certification.certify_genesis_ix_a4_1b_pack3a_runtime import (
    check,
    check_true,
    inspect_database,
    source_contract_checks,
)


class GenesisIXA41BPack3ATests(unittest.TestCase):
    def test_check_passes_on_exact_identity(self) -> None:
        result = check(
            "IDENTITY",
            "Identity",
            expected="core.module.Class",
            actual="core.module.Class",
            detail="Exact module and class identity.",
        )
        self.assertTrue(result.passed)

    def test_check_fails_on_payload_identity(self) -> None:
        result = check(
            "IDENTITY",
            "Identity",
            expected="core.module.Class",
            actual="payload.core.module.Class",
            detail="Payload copies are not canonical.",
        )
        self.assertFalse(result.passed)

    def test_true_check(self) -> None:
        self.assertTrue(
            check_true(
                "BOOL",
                "Boolean",
                actual=True,
                detail="Must be true.",
            ).passed
        )

    def test_missing_database_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = inspect_database(
                Path(directory) / "missing.sqlite"
            )
            self.assertFalse(report["exists"])

    def test_source_contract_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            orchestrator = root / "core/conversation/orchestrator.py"
            catalog = root / "core/knowledge_catalog/search.py"
            runtime = (
                root
                / "core/knowledge_catalog/materialization/search.py"
            )

            orchestrator.parent.mkdir(parents=True)
            catalog.parent.mkdir(parents=True)
            runtime.parent.mkdir(parents=True)

            orchestrator.write_text(
                "grounding = self.grounding_service.ground(context)\n"
                "knowledge_state = self.awareness_service.assess(grounding)\n"
                "synthesis_input = grounding.synthesis_input(synthesis_input)\n"
                "synthesis_input = knowledge_state.synthesis_input(synthesis_input)\n"
                "answer = self.synthesis_handler(synthesis_input)\n",
                encoding="utf-8",
            )
            catalog.write_text(
                "search_runtime_knowledge(query)\n",
                encoding="utf-8",
            )
            runtime.write_text(
                "runtime_chunks_fts MATCH ?\n",
                encoding="utf-8",
            )

            checks = source_contract_checks(root)
            self.assertTrue(all(item.passed for item in checks))


if __name__ == "__main__":
    unittest.main()

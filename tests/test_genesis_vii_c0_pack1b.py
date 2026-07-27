from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.audit import (
    AstPythonParser,
    DeterministicFilesystemScanner,
    DeterministicMarkdownParser,
    RepositoryInventoryBuilder,
    RepositoryInventoryVerifier,
)


class RepositoryAuditFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "fixture"
        (self.root / "pkg").mkdir(parents=True)
        (self.root / "docs" / "architecture").mkdir(parents=True)
        (self.root / "tests").mkdir(parents=True)
        (self.root / "dev" / "verification").mkdir(parents=True)
        (self.root / "pkg" / "__init__.py").write_text('__all__ = ["Example"]\nfrom .module import Example\n', encoding="utf-8")
        (self.root / "pkg" / "module.py").write_text(
            "from dataclasses import dataclass\n"
            "from enum import Enum\n"
            "from typing import Protocol\n\n"
            "class Port(Protocol):\n    def run(self) -> None: ...\n\n"
            "class Mode(Enum):\n    ACTIVE = 'active'\n\n"
            "@dataclass(frozen=True)\nclass Example:\n    value: int\n\n"
            "async def execute() -> None:\n    return None\n",
            encoding="utf-8",
        )
        (self.root / "docs" / "architecture" / "ADR-0001.md").write_text(
            "# Audit Architecture\n\n**Document ID:** ADR-0001\n**Status:** Accepted\n\nSee KM-0000.\n",
            encoding="utf-8",
        )
        (self.root / "tests" / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8")
        (self.root / "dev" / "verification" / "verify_sample.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "ignored").write_text("ignored", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self):
        return RepositoryInventoryBuilder().build(self.root)


class FilesystemTests(RepositoryAuditFixture):
    def test_scanner_is_sorted_and_ignores_vcs_metadata(self) -> None:
        files = DeterministicFilesystemScanner().scan(self.root)
        paths = [item.path for item in files]
        self.assertEqual(paths, sorted(paths))
        self.assertNotIn(".git/ignored", paths)
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(files), len({item.repository_id for item in files}))


class PythonParserTests(RepositoryAuditFixture):
    def test_ast_parser_discovers_supported_symbol_categories(self) -> None:
        files = {item.path: item for item in DeterministicFilesystemScanner().scan(self.root)}
        module = AstPythonParser().parse(self.root, files["pkg/module.py"])
        symbols = {item.name: item for item in module.symbols}
        self.assertTrue(symbols["Port"].is_protocol)
        self.assertTrue(symbols["Mode"].is_enum)
        self.assertTrue(symbols["Example"].is_dataclass)
        self.assertEqual(symbols["execute"].kind.value, "async_function")


class MarkdownParserTests(RepositoryAuditFixture):
    def test_markdown_parser_extracts_identity_and_references(self) -> None:
        files = {item.path: item for item in DeterministicFilesystemScanner().scan(self.root)}
        document = DeterministicMarkdownParser().parse(self.root, files["docs/architecture/ADR-0001.md"])
        self.assertEqual(document.title, "Audit Architecture")
        self.assertEqual(document.document_id, "ADR-0001")
        self.assertEqual(document.status, "Accepted")
        self.assertIn("KM-0000", document.constitutional_references)


class InventoryTests(RepositoryAuditFixture):
    def test_build_is_deterministic(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_statistics_are_consistent(self) -> None:
        inventory = self.build()
        stats = inventory.statistics
        self.assertEqual(stats.python_files, stats.python_modules)
        self.assertEqual(stats.markdown_files, stats.markdown_documents)
        self.assertEqual(stats.total_files, len(inventory.files))
        self.assertEqual(stats.total_bytes, sum(item.size_bytes for item in inventory.files))

    def test_json_outputs_are_stable_and_valid(self) -> None:
        output = self.root.parent / "outputs"
        builder = RepositoryInventoryBuilder()
        first = builder.build(self.root, output)
        first_text = (output / "repository_inventory.json").read_text(encoding="utf-8")
        second = builder.build(self.root, output)
        second_text = (output / "repository_inventory.json").read_text(encoding="utf-8")
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(first_text, second_text)
        parsed = json.loads(first_text)
        self.assertEqual(parsed["fingerprint"], first.fingerprint)


class VerificationTests(RepositoryAuditFixture):
    def test_valid_inventory_passes_certification(self) -> None:
        inventory = self.build()
        verifier = RepositoryInventoryVerifier()
        report = verifier.verify(inventory, root=self.root)
        self.assertTrue(report.passed, report.failed_checks)
        self.assertEqual(report.health.status, "EXCELLENT")
        self.assertEqual(report.health.coverage_percent, 100.0)

    def test_source_mutation_is_detected(self) -> None:
        inventory = self.build()
        (self.root / "pkg" / "module.py").write_text("value = 2\n", encoding="utf-8")
        report = RepositoryInventoryVerifier().verify(inventory, root=self.root)
        checks = {item.check_id: item for item in report.checks}
        self.assertFalse(checks["SOURCE-HASHES"].passed)

    def test_manifest_and_reports_are_serializable(self) -> None:
        inventory = self.build()
        verifier = RepositoryInventoryVerifier()
        report = verifier.verify(inventory, root=self.root)
        manifest = verifier.build_manifest(inventory, report)
        output = self.root.parent / "certification"
        verifier.write_outputs(report, manifest, output)
        self.assertTrue((output / "verification_report.json").is_file())
        self.assertTrue((output / "manifest.json").is_file())
        self.assertTrue((output / "certification_report.md").is_file())
        data = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(data["verification_passed"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.audit import (
    DeterministicFilesystemScanner, EvidenceClass, RepositoryInventoryBuilder,
    RepositoryInventoryVerifier, ScanPolicy, classify_evidence,
)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name) / "repo"
        (self.root / "pkg").mkdir(parents=True); (self.root / "docs").mkdir(); (self.root / "artifacts" / "audit").mkdir(parents=True)
        (self.root / "pkg" / "a.py").write_text("class A:\n    pass\n", encoding="utf-8")
        (self.root / "docs" / "README.md").write_text("# Readme\n", encoding="utf-8")
        (self.root / "artifacts" / "audit" / "result.json").write_text('{"run": 1}\n', encoding="utf-8")
    def tearDown(self): self.tmp.cleanup()


class EvidenceClassificationTests(Fixture):
    def test_classifier(self):
        self.assertIs(classify_evidence("core/a.py"), EvidenceClass.SOURCE)
        self.assertIs(classify_evidence("artifacts/a.json"), EvidenceClass.GENERATED)
        self.assertIs(classify_evidence("vendor/lib.py"), EvidenceClass.EXTERNAL)

    def test_default_policy_excludes_generated_roots_from_canonical_inventory(self):
        inventory = RepositoryInventoryBuilder().build(self.root)
        self.assertNotIn("artifacts/audit/result.json", {x.path for x in inventory.files})
        self.assertEqual(inventory.statistics.generated_files, 0)

    def test_custom_policy_can_inventory_generated_files_with_classification(self):
        policy = ScanPolicy(ignored_directory_names=frozenset({".git", "__pycache__"}))
        inventory = RepositoryInventoryBuilder(filesystem_scanner=DeterministicFilesystemScanner(policy)).build(self.root)
        entry = next(x for x in inventory.files if x.path == "artifacts/audit/result.json")
        self.assertIs(entry.evidence_class, EvidenceClass.GENERATED)

    def test_generated_mutation_does_not_fail_source_hash_check(self):
        policy = ScanPolicy(ignored_directory_names=frozenset({".git", "__pycache__"}))
        inventory = RepositoryInventoryBuilder(filesystem_scanner=DeterministicFilesystemScanner(policy)).build(self.root)
        (self.root / "artifacts" / "audit" / "result.json").write_text('{"run": 2}\n', encoding="utf-8")
        report = RepositoryInventoryVerifier().verify(inventory, root=self.root)
        checks = {c.check_id: c for c in report.checks}
        self.assertTrue(checks["SOURCE-HASHES"].passed)

    def test_source_mutation_still_fails(self):
        inventory = RepositoryInventoryBuilder().build(self.root)
        (self.root / "pkg" / "a.py").write_text("value = 2\n", encoding="utf-8")
        checks = {c.check_id: c for c in RepositoryInventoryVerifier().verify(inventory, root=self.root).checks}
        self.assertFalse(checks["SOURCE-HASHES"].passed)

    def test_schema_is_1_1_0(self):
        self.assertEqual(RepositoryInventoryBuilder().build(self.root).schema_version, "1.1.0")

    def test_artifact_validation(self):
        output = self.root.parent / "out"; builder = RepositoryInventoryBuilder(); inventory = builder.build(self.root)
        report = RepositoryInventoryVerifier().verify(inventory, root=self.root); verifier = RepositoryInventoryVerifier()
        builder.write_outputs(inventory, output); verifier.write_outputs(report, verifier.build_manifest(inventory, report), output)
        checks = verifier.verify_artifacts(output, inventory)
        self.assertTrue(all(c.passed for c in checks), checks)
        self.assertEqual(json.loads((output / "manifest.json").read_text())["inventory_schema_version"], "1.1.0")

    def test_repeated_output_generation_does_not_change_inventory(self):
        output = self.root / "artifacts" / "audit" / "km0000-r1"; builder = RepositoryInventoryBuilder()
        first = builder.build(self.root); builder.write_outputs(first, output)
        second = builder.build(self.root); builder.write_outputs(second, output)
        third = builder.build(self.root)
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(second.fingerprint, third.fingerprint)


if __name__ == "__main__": unittest.main()

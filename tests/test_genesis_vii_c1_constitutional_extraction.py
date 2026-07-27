from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.governance.audit import RepositoryInventoryBuilder
from core.governance.constitution.extraction import (
    ClaimModality,
    ConstitutionalDomain,
    ConstitutionalExtractionEngine,
    ExtractionPolicy,
)


class ConstitutionalExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/constitution").mkdir(parents=True)
        (self.root / "docs/architecture").mkdir(parents=True)
        (self.root / "docs/constitution/KM-0000.md").write_text(
            """**Document ID:** KM-0000
**Status:** Ratified

# Knowledge Constitution

## Provenance

Every knowledge claim must retain source provenance.

The system shall not present unsupported claims as established fact.
""",
            encoding="utf-8",
        )
        (self.root / "docs/architecture/runtime.md").write_text(
            """# Runtime Architecture

Verification should remain deterministic.
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def extract(self, output: bool = False):
        inventory = RepositoryInventoryBuilder().build(self.root)
        directory = self.root / "artifacts/extraction" if output else None
        return ConstitutionalExtractionEngine().extract(root=self.root, inventory=inventory, output_directory=directory)

    def test_extracts_normative_claims(self):
        report = self.extract()
        self.assertEqual(3, report.statistics.claims)
        self.assertTrue(any(item.modality is ClaimModality.MUST for item in report.claims))
        self.assertTrue(any(item.modality is ClaimModality.SHALL_NOT for item in report.claims))

    def test_infers_knowledge_domain(self):
        report = self.extract()
        claim = next(item for item in report.claims if "provenance" in item.normalized_text)
        self.assertIs(claim.domain, ConstitutionalDomain.KNOWLEDGE)

    def test_claim_ids_are_stable(self):
        first = self.extract()
        second = self.extract()
        self.assertEqual([x.claim_id for x in first.claims], [x.claim_id for x in second.claims])
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_outputs_are_complete_and_valid(self):
        report = self.extract(output=True)
        output = self.root / "artifacts/extraction"
        expected = {
            "constitutional_extraction.json", "constitutional_claims.json",
            "constitutional_sources.json", "constitutional_extraction_report.md",
        }
        self.assertEqual(expected, {item.name for item in output.iterdir()})
        payload = json.loads((output / "constitutional_extraction.json").read_text(encoding="utf-8"))
        self.assertEqual(report.fingerprint, payload["fingerprint"])

    def test_generated_outputs_do_not_change_repository_inventory(self):
        builder = RepositoryInventoryBuilder()
        first = builder.build(self.root)
        ConstitutionalExtractionEngine().extract(root=self.root, inventory=first, output_directory=self.root / "artifacts/extraction")
        second = builder.build(self.root)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_policy_can_include_declarations(self):
        path = self.root / "docs/constitution/KM-0000.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nKnowledge is permanent.\n",
            encoding="utf-8",
        )
        inventory = RepositoryInventoryBuilder().build(self.root)
        report = ConstitutionalExtractionEngine(
            ExtractionPolicy(include_non_normative_declarations=True)
        ).extract(root=self.root, inventory=inventory)
        self.assertTrue(any(item.text == "Knowledge is permanent." for item in report.claims))

    def test_code_fences_are_not_extracted(self):
        path = self.root / "docs/constitution/KM-0000.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n```\nThe system must explode.\n```\n",
            encoding="utf-8",
        )
        report = self.extract()
        self.assertFalse(any("explode" in item.normalized_text for item in report.claims))

    def test_public_api(self):
        from core.governance.constitution import ConstitutionalExtractionEngine as PublicEngine
        self.assertIs(PublicEngine, ConstitutionalExtractionEngine)


if __name__ == "__main__":
    unittest.main()

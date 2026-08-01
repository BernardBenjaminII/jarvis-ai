from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.compliance import (
    COMPLIANCE_SCHEMA_VERSION,
    ConstitutionalComplianceEngine,
    ConstitutionalComplianceReporter,
    CompliancePolicy,
)


class ConstitutionalComplianceTests(unittest.TestCase):
    def _ratification_fixture(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        articles = [
            {
                "article_id": "ARTICLE-0001",
                "canonical_text": "Every operation must preserve evidence.",
                "domain": "evidence",
                "status": "ratified",
                "authority": "constitution",
                "authority_rank": 700,
                "fingerprint": "article-a",
            },
            {
                "article_id": "ARTICLE-0002",
                "canonical_text": "Knowledge must retain provenance.",
                "domain": "knowledge",
                "status": "ratified",
                "authority": "constitution",
                "authority_rank": 700,
                "fingerprint": "article-b",
            },
        ]
        (root / "constitutional_ratification.json").write_text(
            json.dumps(
                {
                    "repository_fingerprint": "repo-fp",
                    "extraction_fingerprint": "extract-fp",
                    "analysis_fingerprint": "analysis-fp",
                    "ratification_fingerprint": "ratify-fp",
                }
            ),
            encoding="utf-8",
        )
        (root / "constitutional_registry.json").write_text(
            json.dumps({"articles": articles}),
            encoding="utf-8",
        )
        return root

    def _subject_fixture(self, path: Path) -> Path:
        path.write_text(
            json.dumps(
                {
                    "subjects": [
                        {
                            "subject_id": "SUBJECT-1",
                            "subject_type": "proposal",
                            "path": "docs/proposals/preserve.md",
                            "title": "Preserve evidence",
                            "content": "Every operation must preserve evidence.",
                            "domain": "evidence",
                        },
                        {
                            "subject_id": "SUBJECT-2",
                            "subject_type": "proposal",
                            "path": "docs/proposals/delete.md",
                            "title": "Delete evidence",
                            "content": "Every operation must not preserve evidence.",
                            "domain": "evidence",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_schema(self):
        self.assertEqual(COMPLIANCE_SCHEMA_VERSION, "1.0.0")

    def test_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ratification = self._ratification_fixture(root / "c3")
            subjects = self._subject_fixture(root / "subjects.json")
            engine = ConstitutionalComplianceEngine()
            first = engine.assess(ratification, subjects)
            second = engine.assess(ratification, subjects)
            self.assertEqual(first.compliance_fingerprint, second.compliance_fingerprint)
            self.assertEqual(first.findings, second.findings)

    def test_fingerprint_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalComplianceEngine().assess(
                self._ratification_fixture(root / "c3"),
                self._subject_fixture(root / "subjects.json"),
            )
            self.assertEqual(result.repository_fingerprint, "repo-fp")
            self.assertEqual(result.extraction_fingerprint, "extract-fp")
            self.assertEqual(result.analysis_fingerprint, "analysis-fp")
            self.assertEqual(result.ratification_fingerprint, "ratify-fp")

    def test_compliant_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalComplianceEngine().assess(
                self._ratification_fixture(root / "c3"),
                self._subject_fixture(root / "subjects.json"),
            )
            assessment = next(item for item in result.assessments if item.subject_id == "SUBJECT-1")
            self.assertEqual(assessment.overall_status, "compliant")

    def test_noncompliant_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalComplianceEngine().assess(
                self._ratification_fixture(root / "c3"),
                self._subject_fixture(root / "subjects.json"),
            )
            assessment = next(item for item in result.assessments if item.subject_id == "SUBJECT-2")
            self.assertEqual(assessment.overall_status, "noncompliant")

    def test_unique_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalComplianceEngine().assess(
                self._ratification_fixture(root / "c3"),
                self._subject_fixture(root / "subjects.json"),
            )
            identifiers = [item.finding_id for item in result.findings]
            self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_policy_changes_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ratification = self._ratification_fixture(root / "c3")
            subjects = self._subject_fixture(root / "subjects.json")
            engine = ConstitutionalComplianceEngine()
            first = engine.assess(ratification, subjects)
            second = engine.assess(
                ratification,
                subjects,
                CompliancePolicy(minimum_match_score=0.50),
            )
            self.assertNotEqual(first.compliance_fingerprint, second.compliance_fingerprint)

    def test_reporter_writes_canonical_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalComplianceEngine().assess(
                self._ratification_fixture(root / "c3"),
                self._subject_fixture(root / "subjects.json"),
            )
            written = ConstitutionalComplianceReporter().write(result, root / "c4")
            self.assertEqual(
                {path.name for path in written},
                {
                    "constitutional_compliance.json",
                    "constitutional_compliance_subjects.json",
                    "constitutional_compliance_findings.json",
                    "constitutional_compliance_assessments.json",
                    "constitutional_compliance_traceability.json",
                    "constitutional_compliance_report.md",
                },
            )
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

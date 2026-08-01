from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.certification import (
    CERTIFICATION_SCHEMA_VERSION,
    ConstitutionalCertificationEngine,
    ConstitutionalCertificationReporter,
    build_foundational_scenarios,
)


class CertificationFrameworkTests(unittest.TestCase):
    def _assessment(self):
        return ConstitutionalCertificationEngine().assess_framework(
            repository_fingerprint="repo",
            extraction_fingerprint="extract",
            analysis_fingerprint="analysis",
            ratification_fingerprint="ratify",
            compliance_fingerprint="comply",
        )

    def test_schema_version(self):
        self.assertEqual(CERTIFICATION_SCHEMA_VERSION, "1.0.0")

    def test_scenarios_are_unique(self):
        scenarios = build_foundational_scenarios()
        identifiers = [item.scenario_id for item in scenarios]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_expected_scenario_count(self):
        self.assertEqual(len(build_foundational_scenarios()), 8)

    def test_framework_determinism(self):
        first = self._assessment()
        second = self._assessment()
        self.assertEqual(first.certification_fingerprint, second.certification_fingerprint)
        self.assertEqual(first.results, second.results)

    def test_fingerprint_chain(self):
        result = self._assessment()
        self.assertEqual(result.repository_fingerprint, "repo")
        self.assertEqual(result.extraction_fingerprint, "extract")
        self.assertEqual(result.analysis_fingerprint, "analysis")
        self.assertEqual(result.ratification_fingerprint, "ratify")
        self.assertEqual(result.compliance_fingerprint, "comply")

    def test_pack1_scenarios_are_explicitly_skipped(self):
        result = self._assessment()
        self.assertTrue(result.results)
        self.assertTrue(all(item.status == "skipped" for item in result.results))
        self.assertEqual(result.statistics.failed, 0)

    def test_policy_is_embedded(self):
        result = self._assessment()
        self.assertEqual(result.policy.minimum_positive_findings, 1)
        self.assertTrue(result.policy.require_determinism)

    def test_reporter_writes_canonical_artifacts(self):
        result = self._assessment()
        with tempfile.TemporaryDirectory() as tmp:
            written = ConstitutionalCertificationReporter().write(result, Path(tmp))
            self.assertEqual(
                {path.name for path in written},
                {
                    "constitutional_certification.json",
                    "constitutional_certification_policy.json",
                    "constitutional_certification_traceability.json",
                    "constitutional_certification_report.md",
                },
            )
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

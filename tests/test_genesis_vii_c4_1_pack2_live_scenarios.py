from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.certification import (
    ConstitutionalCertificationEngine,
    ConstitutionalCertificationReporter,
    build_live_certification_scenarios,
)
from core.governance.constitution.compliance.models import ArticleReference


ARTICLE = ArticleReference(
    article_id="ARTICLE-0001",
    canonical_text=(
        "Constitutional evidence must remain preserved, traceable, reviewable, "
        "deterministic, attributable, durable, and available for governance."
    ),
    domain="governance",
    status="ratified",
    authority="constitution",
    authority_rank=1,
    fingerprint="article-fingerprint",
)


def write_ratification(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "constitutional_ratification.json").write_text(
        json.dumps(
            {
                "repository_fingerprint": "repo",
                "extraction_fingerprint": "extract",
                "analysis_fingerprint": "analysis",
                "ratification_fingerprint": "ratify",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (directory / "constitutional_registry.json").write_text(
        json.dumps({"articles": [ARTICLE.to_dict()]}, indent=2),
        encoding="utf-8",
    )


class LiveScenarioTests(unittest.TestCase):
    def test_generates_four_live_scenarios(self):
        scenarios = build_live_certification_scenarios((ARTICLE,))
        self.assertEqual(len(scenarios), 4)
        self.assertEqual(
            {item.expected_status for item in scenarios},
            {"compliant", "noncompliant", "review_required", "not_applicable"},
        )

    def test_generation_is_deterministic(self):
        self.assertEqual(
            build_live_certification_scenarios((ARTICLE,)),
            build_live_certification_scenarios((ARTICLE,)),
        )

    def test_live_execution_produces_all_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_ratification(directory)
            result = ConstitutionalCertificationEngine().assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
        self.assertEqual(result.statistics.scenarios, 4)
        self.assertEqual(result.statistics.passed, 4)
        self.assertEqual(result.statistics.failed, 0)
        self.assertGreaterEqual(result.statistics.positive_findings, 1)
        self.assertGreaterEqual(result.statistics.negative_findings, 1)
        self.assertGreaterEqual(result.statistics.review_findings, 1)
        self.assertEqual(result.statistics.not_applicable_subjects, 1)

    def test_expected_article_is_rank_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_ratification(directory)
            result = ConstitutionalCertificationEngine().assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
        applicable = [
            item
            for item in result.results
            if item.observed_status != "not_applicable"
        ]
        self.assertTrue(applicable)
        self.assertTrue(all(item.rank == 1 for item in applicable))

    def test_live_execution_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_ratification(directory)
            engine = ConstitutionalCertificationEngine()
            first = engine.assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
            second = engine.assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
        self.assertEqual(
            first.certification_fingerprint,
            second.certification_fingerprint,
        )
        self.assertEqual(first.results, second.results)

    def test_traceability_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_ratification(directory)
            result = ConstitutionalCertificationEngine().assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
        self.assertTrue(all(item.traceability_complete for item in result.results))

    def test_reporter_writes_pack2_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ratification = root / "ratification"
            output = root / "output"
            write_ratification(ratification)
            result = ConstitutionalCertificationEngine().assess_live_scenarios(
                ratification_directory=ratification,
                compliance_fingerprint="comply",
            )
            written = ConstitutionalCertificationReporter().write(result, output)
        self.assertEqual(len(written), 5)

    def test_no_diagnostics_for_certified_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_ratification(directory)
            result = ConstitutionalCertificationEngine().assess_live_scenarios(
                ratification_directory=directory,
                compliance_fingerprint="comply",
            )
        self.assertEqual(result.diagnostics, ())


if __name__ == "__main__":
    unittest.main()

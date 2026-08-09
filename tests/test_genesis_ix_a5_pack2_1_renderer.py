from __future__ import annotations

import json
import unittest

from dev.reports import (
    AuditReport,
    EngineeringReportRenderer,
    EngineeringReportStatus,
)


class GenesisIXA5Pack21Tests(unittest.TestCase):
    def make_report(self) -> AuditReport:
        return AuditReport(
            schema_version="1",
            status=EngineeringReportStatus.PASSED,
            classification="TEST",
            title="Renderer Test",
            summary={
                "database_path": "/tmp/catalog.sqlite",
                "fts_rows": 4,
            },
            recommendations=(
                "Continue.",
            ),
        )

    def test_markdown_renderer(self) -> None:
        text = (
            EngineeringReportRenderer.render_markdown(
                self.make_report()
            )
        )

        self.assertIn(
            "Renderer Test",
            text,
        )
        self.assertIn(
            "database_path",
            text,
        )

    def test_json_renderer(self) -> None:
        payload = json.loads(
            EngineeringReportRenderer.render_json(
                self.make_report()
            )
        )

        self.assertEqual(
            payload["classification"],
            "TEST",
        )

    def test_terminal_renderer(self) -> None:
        text = (
            EngineeringReportRenderer.render_terminal(
                self.make_report()
            )
        )

        self.assertIn(
            "RENDERER TEST",
            text,
        )
        self.assertIn(
            "Status",
            text,
        )

    def test_summary_renderer(self) -> None:
        summary = (
            EngineeringReportRenderer.render_summary(
                self.make_report()
            )
        )

        self.assertTrue(summary["passed"])
        self.assertEqual(
            summary["status"],
            "PASSED",
        )

    def test_legacy_dict_renderer(self) -> None:
        text = (
            EngineeringReportRenderer.render_markdown(
                {
                    "status": "FAILED",
                    "classification": "LEGACY",
                    "summary": {
                        "database_path": "/tmp/legacy.sqlite"
                    },
                }
            )
        )

        self.assertIn(
            "LEGACY",
            text,
        )


if __name__ == "__main__":
    unittest.main()

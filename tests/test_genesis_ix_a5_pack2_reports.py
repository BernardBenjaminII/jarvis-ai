from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError

from dev.reports import (
    AuditReport,
    EngineeringReportStatus,
    normalize_report,
)


class GenesisIXA5Pack2Tests(unittest.TestCase):
    def test_report_is_immutable(self) -> None:
        report = AuditReport(
            schema_version="1",
            status=EngineeringReportStatus.PASSED,
            classification="TEST",
            title="Test",
        )

        with self.assertRaises(FrozenInstanceError):
            report.title = "Changed"

    def test_dict_normalization(self) -> None:
        report = normalize_report(
            {
                "status": "PASS",
                "classification": "LEGACY",
                "summary": {"value": 1},
            },
            title="Legacy",
        )

        self.assertIsInstance(report, AuditReport)
        self.assertTrue(report.passed)
        self.assertEqual(
            report.summary["value"],
            1,
        )

    def test_object_normalization(self) -> None:
        class Legacy:
            def to_dict(self):
                return {
                    "status": "FAILED",
                    "classification": "DATA",
                }

        report = normalize_report(
            Legacy(),
            title="Legacy Object",
        )

        self.assertEqual(
            report.status,
            EngineeringReportStatus.FAILED,
        )

    def test_json_deterministic(self) -> None:
        report = normalize_report(
            {
                "status": "PASSED",
                "classification": "TEST",
                "summary": {"b": 2, "a": 1},
            },
            title="Deterministic",
        )

        first = report.to_json()
        second = report.to_json()

        self.assertEqual(first, second)
        self.assertEqual(
            json.loads(first)["summary"],
            {"a": 1, "b": 2},
        )

    def test_existing_report_is_idempotent(self) -> None:
        report = AuditReport(
            schema_version="1",
            status=EngineeringReportStatus.PASSED,
            classification="TEST",
            title="Test",
        )

        self.assertIs(
            normalize_report(report),
            report,
        )


if __name__ == "__main__":
    unittest.main()

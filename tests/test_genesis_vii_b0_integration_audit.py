
from pathlib import Path
import tempfile
import unittest

from core.executive.integration_audit import (
    IntegrationAuditReport,
    IntegrationAuditor,
    IntegrationFinding,
    IntegrationStatus,
)


class GenesisVIIB0IntegrationAuditTests(unittest.TestCase):
    def test_report_is_deterministic(self):
        finding = IntegrationFinding(
            "a", "runtime", "python", IntegrationStatus.PASS, "available"
        )
        first = IntegrationAuditReport("1.0.0", "Genesis VII-B0", (finding,))
        second = IntegrationAuditReport("1.0.0", "Genesis VII-B0", (finding,))
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_fail_dominates(self):
        report = IntegrationAuditReport(
            "1.0.0", "Genesis VII-B0",
            (
                IntegrationFinding("a", "a", "a", IntegrationStatus.PASS, "pass"),
                IntegrationFinding("b", "b", "b", IntegrationStatus.FAIL, "fail"),
            ),
        )
        self.assertEqual(report.overall_status, IntegrationStatus.FAIL)

    def test_partial_dominates_pass(self):
        report = IntegrationAuditReport(
            "1.0.0", "Genesis VII-B0",
            (
                IntegrationFinding("a", "a", "a", IntegrationStatus.PASS, "pass"),
                IntegrationFinding("b", "b", "b", IntegrationStatus.PARTIAL, "partial"),
            ),
        )
        self.assertEqual(report.overall_status, IntegrationStatus.PARTIAL)

    def test_path_audit_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "example.txt"
            path.write_text("unchanged", encoding="utf-8")
            finding = IntegrationAuditor(root)._path_finding(
                "path", "test", "file", "example.txt"
            )
            self.assertEqual(finding.status, IntegrationStatus.PASS)
            self.assertEqual(path.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()

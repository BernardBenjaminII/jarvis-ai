from __future__ import annotations

import importlib.util
import json
import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITOR_PATH = ROOT / "dev/tools/audit_genesis_3f1.py"
SPEC = importlib.util.spec_from_file_location("audit_genesis_3f1", AUDITOR_PATH)
assert SPEC and SPEC.loader
AUDITOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDITOR
SPEC.loader.exec_module(AUDITOR)


class Genesis3F1Tests(unittest.TestCase):
    def test_canonical_packages_are_present(self) -> None:
        for package in AUDITOR.CANONICAL_PACKAGES:
            self.assertTrue((ROOT / package).is_dir(), package)

    def test_every_canonical_package_has_modules(self) -> None:
        for package in AUDITOR.CANONICAL_PACKAGES:
            modules = AUDITOR.package_modules(ROOT, package)
            self.assertGreater(len(modules), 0)

    def test_module_audit_is_deterministic(self) -> None:
        first = AUDITOR.build_reports(ROOT)
        second = AUDITOR.build_reports(ROOT)
        self.assertEqual(first, second)

    def test_freeze_reports_are_current(self) -> None:
        reports = AUDITOR.build_reports(ROOT)
        self.assertEqual(AUDITOR.check_reports(ROOT, reports), [])

    def test_snapshot_has_no_dependency_violations(self) -> None:
        snapshot = json.loads(
            (ROOT / "docs/architecture/convergence/genesis_3f1_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(snapshot["dependency_graph"]["violations"], [])

    def test_snapshot_has_stable_fingerprint(self) -> None:
        snapshot = json.loads(
            (ROOT / "docs/architecture/convergence/genesis_3f1_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        fingerprint = snapshot["architecture_fingerprint"]
        self.assertEqual(len(fingerprint), 64)
        int(fingerprint, 16)

    def test_public_api_contains_workspace_and_integration(self) -> None:
        report = json.loads(
            (ROOT / "docs/architecture/convergence/genesis_3f1_public_api.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("core.cognition.workspace", report["packages"])
        self.assertIn("core.cognition.integration", report["packages"])

    def test_write_and_check_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            reports = {"reports/a.txt": "alpha\n", "reports/b.json": "{}\n"}
            AUDITOR.write_reports(target, reports)
            self.assertEqual(AUDITOR.check_reports(target, reports), [])


if __name__ == "__main__":
    unittest.main()

"""Genesis IV-B4 definition/export audit-correction tests."""

from __future__ import annotations

from pathlib import Path
import unittest

from core.observation.audit import audit_observation_definitions
from core.observation.export_audit import (
    module_defines_observation,
    scan_observation_exports,
)


ROOT = Path(__file__).resolve().parents[1]


class GenesisIVB4AuditCorrectionTests(unittest.TestCase):
    def test_direct_definition_is_detected(self) -> None:
        self.assertTrue(
            module_defines_observation(
                ROOT / "core/cognition/common/contracts.py"
            )
        )

    def test_reexport_is_not_definition(self) -> None:
        self.assertFalse(
            module_defines_observation(
                ROOT / "core/cognition/contracts.py"
            )
        )

    def test_reexport_is_in_public_export_inventory(self) -> None:
        exports = scan_observation_exports(ROOT)
        self.assertTrue(
            any(
                item.path == "core/cognition/contracts.py"
                for item in exports
            )
        )

    def test_governance_inventory_contains_only_direct_definitions(self) -> None:
        report = audit_observation_definitions(ROOT)
        paths = {item.path for item in report.definitions}
        self.assertIn("core/cognition/common/contracts.py", paths)
        self.assertNotIn("core/cognition/contracts.py", paths)

    def test_convergence_has_no_false_duplicate(self) -> None:
        report = audit_observation_definitions(ROOT)
        self.assertFalse(report.forbidden_duplicates)


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations

import importlib
from pathlib import Path
import unittest


class Pack4B3NamespaceConsolidationTests(unittest.TestCase):
    def test_legacy_module_was_migrated(self) -> None:
        self.assertFalse(Path("core/executive/capabilities.py").exists())
        self.assertTrue(Path("core/executive/capability_contracts.py").is_file())

    def test_legacy_readiness_is_reexported(self) -> None:
        from core.executive.capabilities import DirectorReadiness

        self.assertEqual(DirectorReadiness.READY.value, "ready")
        self.assertEqual(DirectorReadiness.DEGRADED.value, "degraded")

    def test_legacy_and_orchestration_exports_coexist(self) -> None:
        from core.executive.capabilities import (
            CapabilityOrchestrator,
            CapabilityRegistry,
            DirectorReadiness,
        )

        self.assertIsNotNone(CapabilityOrchestrator)
        self.assertIsNotNone(CapabilityRegistry)
        self.assertIsNotNone(DirectorReadiness)

    def test_public_api_contains_legacy_and_new_symbols(self) -> None:
        package = importlib.import_module("core.executive.capabilities")
        self.assertIn("DirectorReadiness", package.__all__)
        self.assertIn("CapabilityOrchestrator", package.__all__)
        self.assertIn("CapabilityRegistry", package.__all__)

    def test_executive_director_imports(self) -> None:
        from core.executive.director import ExecutiveDirector

        self.assertIsNotNone(ExecutiveDirector)

    def test_legacy_registry_imports(self) -> None:
        from core.executive.registry import DirectorRegistry

        self.assertIsNotNone(DirectorRegistry)


if __name__ == "__main__":
    unittest.main()

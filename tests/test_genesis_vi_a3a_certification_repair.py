from __future__ import annotations
import importlib
import unittest
from core.integration.bus import ExecutiveProjectionBus
from core.integration.readiness import ReadinessColor

class FakeProjectionService:
    def all_projections(self):
        return {"projections": {"knowledge": {"health": {"status": "available", "summary": "Ready", "warnings": [], "errors": []}}}}

class GenesisVIA3ACertificationRepairTests(unittest.TestCase):
    def test_integration_package_imports(self):
        module = importlib.import_module("core.integration")
        self.assertTrue(hasattr(module, "build_default_integration_runtime"))
        self.assertTrue(hasattr(module, "get_default_integration_runtime"))
        self.assertTrue(hasattr(module, "ExecutiveProjectionBus"))

    def test_existing_contracts_remain_importable(self):
        contracts = importlib.import_module("core.integration.contracts")
        self.assertTrue(hasattr(contracts, "ProjectionEnvelope"))
        self.assertTrue(hasattr(contracts, "ProjectionHealth"))
        self.assertTrue(hasattr(contracts, "ProjectionStatus"))

    def test_bus_is_green(self):
        self.assertEqual(ExecutiveProjectionBus(FakeProjectionService()).snapshot().overall.color, ReadinessColor.GREEN)

    def test_operations_preserves_capabilities_route(self):
        operations = importlib.import_module("core.src.routes.operations")
        paths = {route.path for route in operations.router.routes}
        self.assertIn("/operations/capabilities", paths)

    def test_operations_adds_bridge_routes(self):
        operations = importlib.import_module("core.src.routes.operations")
        paths = {route.path for route in operations.router.routes}
        self.assertIn("/operations/bridge", paths)
        self.assertIn("/operations/bridge/readiness", paths)
        self.assertIn("/operations/bridge/manifest", paths)

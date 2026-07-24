from __future__ import annotations

import unittest

from fastapi import HTTPException

from core.src.routes.operations import (
    executive_bridge_manifest,
    operations_capabilities,
    operations_capability,
    operations_projection,
    operations_projections,
    router,
)


class GenesisVIA3BCompatibilityFinalizationTests(unittest.TestCase):
    def test_ui_a2_routes_are_registered(self) -> None:
        paths = {route.path for route in router.routes}
        expected = {
            "/operations/projections",
            "/operations/projections/{projection_id}",
            "/operations/capabilities",
            "/operations/capabilities/{capability_name}",
        }
        self.assertTrue(expected.issubset(paths))

    def test_bridge_routes_remain_registered(self) -> None:
        paths = {route.path for route in router.routes}
        self.assertIn("/operations/bridge", paths)
        self.assertIn("/operations/bridge/readiness", paths)
        self.assertIn("/operations/bridge/manifest", paths)
        self.assertIn("/operations/bridge/projections/{projection_id}", paths)

    def test_all_projections_uses_canonical_runtime(self) -> None:
        result = operations_projections()
        self.assertIn("projections", result)
        self.assertIn("capabilities", result["projections"])
        self.assertIn("knowledge", result["projections"])
        self.assertIn("operations", result["projections"])

    def test_single_projection_matches_projection_contract(self) -> None:
        result = operations_projection("capabilities")
        self.assertEqual(result["projection_id"], "capabilities")
        self.assertIn("health", result)
        self.assertIn("data", result)

    def test_capabilities_route_is_projection_alias(self) -> None:
        result = operations_capabilities()
        self.assertEqual(result["projection_id"], "capabilities")
        self.assertIsInstance(result["data"]["capabilities"], list)

    def test_named_capability_is_resolved_from_projection(self) -> None:
        capabilities = operations_capabilities()["data"]["capabilities"]
        self.assertGreater(len(capabilities), 0)
        name = capabilities[0]["name"]
        result = operations_capability(name)
        self.assertEqual(result["name"], name)

    def test_unknown_projection_returns_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            operations_projection("missing.projection")
        self.assertEqual(context.exception.status_code, 404)

    def test_unknown_capability_returns_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            operations_capability("missing.capability")
        self.assertEqual(context.exception.status_code, 404)

    def test_bridge_manifest_remains_canonical(self) -> None:
        manifest = executive_bridge_manifest()
        self.assertEqual(
            manifest["projection_endpoint_template"],
            "/operations/bridge/projections/{projection_id}",
        )


if __name__ == "__main__":
    unittest.main()

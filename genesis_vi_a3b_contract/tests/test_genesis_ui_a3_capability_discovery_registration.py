from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from core.capabilities.discovery import CapabilityDiscovery
from core.capabilities.metadata import CapabilityBindingState, metadata_for
from core.capabilities.operations import register_operations_capabilities
from core.capabilities.registry import CapabilityRegistry
from core.integration.bootstrap import build_default_integration_runtime
from core.integration.providers.capabilities import CapabilityProjectionProvider


class FakeValue:
    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {"value": self.value}


class FakeEventRegistry:
    def list_events(self, limit=100):
        return []


class FakeOperationsService:
    def __init__(self):
        self.event_registry = FakeEventRegistry()

    def snapshot(self):
        return FakeValue("status")

    def executive(self):
        return FakeValue("executive")

    def health(self):
        return FakeValue("healthy")

    def missions(self):
        return []

    def resources(self):
        return FakeValue("resources")

    def timeline(self, limit=100):
        return FakeValue("timeline")


class CapabilityDiscoveryRegistrationTests(unittest.TestCase):
    def test_operations_capabilities_are_registered(self) -> None:
        registry = CapabilityRegistry()
        register_operations_capabilities(
            registry,
            FakeOperationsService(),
        )

        names = {
            capability.name
            for capability in registry.all()
        }

        self.assertEqual(len(names), 7)
        self.assertIn("operations.status", names)
        self.assertIn("operations.events", names)

    def test_operations_registration_is_idempotent(self) -> None:
        registry = CapabilityRegistry()
        service = FakeOperationsService()

        register_operations_capabilities(registry, service)
        register_operations_capabilities(registry, service)

        self.assertEqual(len(registry.all()), 7)

    def test_metadata_reports_bound_state(self) -> None:
        registry = CapabilityRegistry()
        register_operations_capabilities(
            registry,
            FakeOperationsService(),
        )

        capability = registry.get("operations.status")
        metadata = metadata_for(capability)

        self.assertEqual(
            metadata.binding_state,
            CapabilityBindingState.BOUND,
        )
        self.assertEqual(metadata.domain, "operations")

    def test_projection_contains_real_bound_capabilities(self) -> None:
        registry = CapabilityRegistry()
        register_operations_capabilities(
            registry,
            FakeOperationsService(),
        )

        projection = CapabilityProjectionProvider(registry).project().to_dict()

        self.assertEqual(projection["health"]["status"], "available")
        self.assertEqual(projection["data"]["total"], 7)
        self.assertEqual(projection["data"]["bound"], 7)
        self.assertEqual(projection["data"]["unbound"], 0)

    def test_default_runtime_registers_builtin_capabilities(self) -> None:
        runtime = build_default_integration_runtime(
            operations_service=FakeOperationsService(),
            capability_packages=[],
        )

        self.assertGreaterEqual(
            len(runtime.capability_registry.all()),
            7,
        )

    def test_recursive_discovery_invokes_package_hook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "fixture_capability_package"
            package.mkdir()
            (package / "__init__.py").write_text(
                "from .registration import register_capabilities\n",
                encoding="utf-8",
            )
            (package / "registration.py").write_text(
                textwrap.dedent(
                    """
                    def register_capabilities(registry):
                        registry.fixture_hook_called = True
                    """
                ),
                encoding="utf-8",
            )

            sys.path.insert(0, directory)
            try:
                registry = CapabilityRegistry()
                results = CapabilityDiscovery(
                    ["fixture_capability_package"]
                ).discover(registry)

                self.assertTrue(
                    getattr(registry, "fixture_hook_called", False)
                )
                self.assertTrue(
                    any(result.discovered for result in results)
                )
            finally:
                sys.path.remove(directory)
                for module_name in list(sys.modules):
                    if module_name.startswith("fixture_capability_package"):
                        del sys.modules[module_name]


if __name__ == "__main__":
    unittest.main()

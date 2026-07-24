from __future__ import annotations
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from core.capabilities.registry import CapabilityRegistry
from core.integration.contracts import ProjectionEnvelope, ProjectionHealth, ProjectionStatus
from core.integration.errors import DuplicateProjectionProviderError, ProjectionProviderNotFoundError
from core.integration.providers.capabilities import CapabilityProjectionProvider
from core.integration.registry import ProjectionRegistry
from core.integration.service import ExecutiveProjectionService

class FixtureCapability:
    name = "fixture.capability"
    order = 10
    requires = set()
    provides = {"fixture.ready"}
    def execute(self, context):
        raise NotImplementedError

@dataclass
class FixtureProvider:
    projection_id: str = "fixture"
    schema_version: str = "1.0"
    def health(self):
        return ProjectionHealth(ProjectionStatus.AVAILABLE, "Fixture is healthy.")
    def project(self):
        return ProjectionEnvelope(self.projection_id, self.schema_version, datetime.now(timezone.utc), self.health(), {"value": 1}, "fixture.provider")

class ExecutiveProjectionFrameworkTests(unittest.TestCase):
    def test_registry_registers_provider(self):
        registry = ProjectionRegistry(); provider = FixtureProvider(); registry.register(provider)
        self.assertIs(registry.get("fixture"), provider)
    def test_registry_rejects_duplicates(self):
        registry = ProjectionRegistry(); registry.register(FixtureProvider())
        with self.assertRaises(DuplicateProjectionProviderError): registry.register(FixtureProvider())
    def test_unknown_provider(self):
        with self.assertRaises(ProjectionProviderNotFoundError): ProjectionRegistry().get("missing")
    def test_service_returns_all(self):
        registry = ProjectionRegistry(); registry.register(FixtureProvider())
        result = ExecutiveProjectionService(registry).all_projections()
        self.assertEqual(result["provider_count"], 1); self.assertEqual(result["summary"]["available"], 1)
    def test_empty_capabilities_not_configured(self):
        result = CapabilityProjectionProvider(CapabilityRegistry()).project().to_dict()
        self.assertEqual(result["health"]["status"], "not_configured")
    def test_capability_metadata(self):
        registry = CapabilityRegistry(); registry.register(FixtureCapability())
        result = CapabilityProjectionProvider(registry).project().to_dict()
        self.assertEqual(result["data"]["capabilities"][0]["provides"], ["fixture.ready"])
        self.assertTrue(result["data"]["dependency_resolution"]["resolvable"])

if __name__ == "__main__": unittest.main()

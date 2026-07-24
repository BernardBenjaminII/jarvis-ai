from importlib import import_module

from dev.doctor.check import HealthCheck


class ServicesCheck(HealthCheck):
    name = "Knowledge Services"
    category = "Knowledge"
    order = 45

    description = "Verifies canonical Knowledge Engine services."
    documentation = "docs/architecture/service_architecture.md"

    REQUIRED_IMPORTS = [
        "knowledge_engine.services.extraction",
        "knowledge_engine.services.chunking",
        "knowledge_engine.services.embeddings",
        "knowledge_engine.services.workflow_registry",
        "knowledge_engine.services.retrieval",
        "knowledge_engine.services.graph",
    ]

    def run(self):
        failures = 0

        for module in self.REQUIRED_IMPORTS:
            try:
                import_module(module)
                self.detail(f"✓ import {module}")
            except Exception as exc:
                self.fail(f"{module}: {exc}")
                failures += 1

        total = len(self.REQUIRED_IMPORTS)
        passed = total - failures
        self.score(round((passed / total) * 100))

        return self.result()

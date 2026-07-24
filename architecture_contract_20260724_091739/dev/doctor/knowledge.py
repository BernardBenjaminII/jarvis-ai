from pathlib import Path
import importlib

from .check import HealthCheck


ROOT = Path(__file__).resolve().parents[2]


class KnowledgeEngineCheck(HealthCheck):

    name = "Knowledge Engine"
    category = "Knowledge"
    order = 30

    description = "Verifies the canonical Knowledge Engine layout."
    fix_hint = "Restore missing Knowledge Engine packages."
    documentation = "docs/architecture/architecture_blueprint.md"

    REQUIRED_PATHS = [
        "knowledge_engine/receiving",
        "knowledge_engine/discovery",
        "knowledge_engine/inspectors",
        "knowledge_engine/extraction",
        "knowledge_engine/processing",
        "knowledge_engine/processors",
        "knowledge_engine/chunking",
        "knowledge_engine/embeddings",
        "knowledge_engine/objects",
        "knowledge_engine/registry",
        "knowledge_engine/knowledge_graph",
        "knowledge_engine/retrieval",
        "knowledge_engine/workflow",
        "knowledge_engine/workflows",
        "knowledge_engine/orchestrator",
        "knowledge_engine/director",
    ]

    REQUIRED_IMPORTS = [
        "knowledge_engine.chunking.builder",
        "knowledge_engine.chunking.chunker",
        "knowledge_engine.embeddings.engine",
        "knowledge_engine.embeddings.provider",
        "knowledge_engine.storage.database",
        "knowledge_engine.storage.migrate",
    ]
    def run(self):

        missing = []

        for item in self.REQUIRED_PATHS:
            path = ROOT / item

            if path.exists():
                self.detail(f"✓ {item}")
            else:
                missing.append(item)

        if missing:
            self.fail(
                "Missing: " + ", ".join(missing)
            )
            self.score(0)
        else:
            self.score(100)

        return self.result()

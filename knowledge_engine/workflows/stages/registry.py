from __future__ import annotations

from knowledge_engine.services.workflow_registry import WorkflowRegistryService
from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class RegistryStage(WorkflowStage):

    name = "Registry"

    def __init__(self):
        self.service = WorkflowRegistryService()

    def run(
        self,
        context: KnowledgeContext,
    ) -> KnowledgeContext:

        if not context.embeddings:
            context.fail("No embeddings available.")
            return context

        context.registry_ids = self.service.register(
            context.chunks
        )

        context.registry_count = len(
            context.registry_ids
        )

        return context

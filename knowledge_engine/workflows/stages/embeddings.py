from __future__ import annotations

from knowledge_engine.services.embeddings import EmbeddingService
from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class EmbeddingStage(WorkflowStage):

    name = "Embeddings"

    def __init__(self):
        self.service = EmbeddingService()

    def run(
        self,
        context: KnowledgeContext,
    ) -> KnowledgeContext:

        if not context.chunks:
            context.fail("No chunks available for embedding.")
            return context

        context.embeddings = self.service.embed_batch(
            context.chunks
        )

        context.embedding_count = len(
            context.embeddings
        )

        return context

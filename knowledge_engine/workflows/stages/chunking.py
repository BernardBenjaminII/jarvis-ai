from __future__ import annotations

from knowledge_engine.services.chunking import ChunkingService
from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class ChunkingStage(WorkflowStage):

    name = "Chunking"

    def __init__(self):
        self.service = ChunkingService()

    def run(
        self,
        context: KnowledgeContext,
    ) -> KnowledgeContext:

        if not context.extracted_text.strip():
            context.fail("No extracted text available.")
            return context

        result = self.service.chunk(
            context.extracted_text,
            file_path=str(context.source_path),
        )

        context.chunks = result.chunks

        context.metadata["chunk_strategy"] = result.strategy

        return context

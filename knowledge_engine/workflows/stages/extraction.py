from __future__ import annotations

from knowledge_engine.services.extraction import ExtractionService
from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class ExtractionStage(WorkflowStage):
    name = "Extraction"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        text, processor, status, error = ExtractionService.extract(
            context.source_path
        )

        context.metadata["processor"] = processor
        context.metadata["status"] = status

        if error:
            context.fail(error)
            return context

        context.raw_text = text
        context.extracted_text = text

        return context

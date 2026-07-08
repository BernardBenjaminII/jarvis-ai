from __future__ import annotations

from .context import KnowledgeContext
from .stage import WorkflowStage


class ReceiveTextStage(WorkflowStage):
    name = "Receiving"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        if not context.source_path.exists():
            context.fail(f"Missing source file: {context.source_path}")
            return context

        context.content_type = "text/plain"
        context.metadata["filename"] = context.source_path.name
        return context


class ExtractTextStage(WorkflowStage):
    name = "Extraction"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        try:
            context.raw_text = context.source_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            context.extracted_text = context.raw_text
        except Exception as exc:
            context.fail(f"Text extraction failed: {exc}")

        return context


class ChunkTextStage(WorkflowStage):
    name = "Chunking"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        text = context.extracted_text.strip()

        if not text:
            context.fail("No extracted text available for chunking.")
            return context

        context.chunks = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        if not context.chunks:
            context.fail("Chunking produced no chunks.")

        return context


class MockEmbeddingStage(WorkflowStage):
    name = "Embeddings"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        if not context.chunks:
            context.fail("No chunks available for embedding.")
            return context

        context.embeddings = [
            {
                "chunk_index": index,
                "dimension": 3,
                "vector": [float(index), 0.0, 1.0],
            }
            for index, _ in enumerate(context.chunks)
        ]

        return context


class MockRegistryStage(WorkflowStage):
    name = "Registry"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        if not context.embeddings:
            context.fail("No embeddings available for registry.")
            return context

        context.registry_ids = [
            f"fixture-registry-{index}"
            for index, _ in enumerate(context.embeddings)
        ]

        return context


class MockRetrievalStage(WorkflowStage):
    name = "Retrieval"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        if not context.registry_ids:
            context.fail("No registry ids available for retrieval.")
            return context

        context.metadata["retrieval_verified"] = True
        return context

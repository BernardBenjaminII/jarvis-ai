from __future__ import annotations

from knowledge_engine.embeddings.builder import ChunkEmbeddingBuilder

from knowledge_engine.director.stage import (
    AssimilationStage,
    StageResult,
)


class EmbeddingStage(AssimilationStage):

    name = "Embedding Builder"

    order = 700

    def run(self, context):

        builder = ChunkEmbeddingBuilder(context.database)

        metrics = builder.build_pending_embeddings()

        return StageResult(

            name=self.name,

            success=True,

            metrics=metrics,
        )

from __future__ import annotations

from knowledge_engine.chunking.builder import ChunkBuilder

from knowledge_engine.director.stage import (
    AssimilationStage,
    StageResult,
)


class ChunkStage(AssimilationStage):

    name = "Chunk Builder"

    order = 600

    def run(self, context):

        builder = ChunkBuilder(context.database)

        metrics = builder.build()

        return StageResult(

            name=self.name,

            success=True,

            metrics=metrics,
        )

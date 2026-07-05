from __future__ import annotations


class StageRegistry:

    def __init__(self):

        self._stages = []

    def register(self, stage):

        self._stages.append(stage)

        self._stages.sort(key=lambda s: s.order)

    @property
    def stages(self):

        return list(self._stages)

    def register_defaults(self):

        from knowledge_engine.director.stages.chunking import ChunkStage

        from knowledge_engine.director.stages.embeddings import EmbeddingStage

        from knowledge_engine.director.stages.faiss import FAISSStage

        from knowledge_engine.director.stages.graph import GraphStage

        from knowledge_engine.director.stages.doctor import DoctorStage

        self.register(ChunkStage())

        self.register(EmbeddingStage())

        self.register(FAISSStage())

        self.register(GraphStage())

        self.register(DoctorStage())

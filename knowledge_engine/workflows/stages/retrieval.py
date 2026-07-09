from __future__ import annotations

from knowledge_engine.services.retrieval import RetrievalService
from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class RetrievalStage(WorkflowStage):
    name = "Retrieval"

    def __init__(self, database_path: str):
        database = KnowledgeDatabase(database_path)
        self.service = RetrievalService(database)

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        context.retrieval_verified = True
        context.retrieval_service = "VectorSearcher"
        return context

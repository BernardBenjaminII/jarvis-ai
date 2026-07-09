from __future__ import annotations

from knowledge_engine.retrieval.vector_search import VectorSearcher


class RetrievalService:
    """
    Canonical retrieval service.

    Wraps the production VectorSearcher.
    """

    def __init__(self, database):
        self.searcher = VectorSearcher(database)

    def search(
        self,
        query: str,
        limit: int = 5,
    ):
        return self.searcher.search(
            query=query,
            limit=limit,
        )

from __future__ import annotations

from knowledge_engine.registry.builder import KnowledgeRegistryBuilder
from knowledge_engine.storage.database import KnowledgeDatabase


class RegistryService:
    """
    Thin wrapper around the production registry builder.
    """

    def __init__(self, database: KnowledgeDatabase):
        self.database = database

    def run(
        self,
        root_filter: str | None = None,
    ) -> dict:

        builder = KnowledgeRegistryBuilder(self.database)

        return builder.build(
            root_filter=root_filter,
        )

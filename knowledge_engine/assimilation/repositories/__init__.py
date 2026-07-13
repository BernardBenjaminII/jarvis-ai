"""
Persistence repositories used by JARVIS controlled assimilation.

Repositories own SQL and database-record mapping.

Handlers own object-specific workflow.
Services own focused business operations.
Directors own orchestration and scheduling.
"""

from knowledge_engine.assimilation.repositories.knowledge_registry import (
    KnowledgeRegistryRepository,
)

__all__ = [
    "KnowledgeRegistryRepository",
]

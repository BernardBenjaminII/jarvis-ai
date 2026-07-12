"""
Canonical JARVIS assimilation handlers.
"""

from knowledge_engine.assimilation.handlers.base import (
    AssimilationHandler,
)
from knowledge_engine.assimilation.handlers.single_document import (
    SingleDocumentHandler,
)
from knowledge_engine.assimilation.handlers.source_collection import (
    SourceCollectionHandler,
)

__all__ = [
    "AssimilationHandler",
    "SingleDocumentHandler",
    "SourceCollectionHandler",
]

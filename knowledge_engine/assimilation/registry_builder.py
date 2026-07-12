"""
Construction of the canonical JARVIS assimilation handler registry.
"""

from __future__ import annotations

from knowledge_engine.assimilation.handler_registry import (
    HandlerRegistry,
)
from knowledge_engine.assimilation.handlers.single_document import (
    SingleDocumentHandler,
)
from knowledge_engine.assimilation.handlers.source_collection import (
    SourceCollectionHandler,
)
from knowledge_engine.assimilation.runner import AssimilationRunner


def build_handler_registry(
    runner: AssimilationRunner,
) -> HandlerRegistry:
    """
    Construct the complete assimilation handler registry.

    The Director obtains concrete handlers only through this builder.
    """

    registry = HandlerRegistry()

    registry.register(
        SingleDocumentHandler(runner)
    )

    registry.register(
        SourceCollectionHandler(runner.db)
    )

    return registry

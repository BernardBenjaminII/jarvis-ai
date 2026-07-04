from __future__ import annotations

from pathlib import Path

from knowledge_engine.processors.base import BaseProcessor
from knowledge_engine.processors.document import DocumentProcessor
from knowledge_engine.processors.source_code import SourceCodeProcessor


class ProcessorRegistry:
    def __init__(self):
        self.processors: list[BaseProcessor] = []

    def register(self, processor: BaseProcessor) -> None:
        self.processors.append(processor)

    def get(self, path: Path) -> BaseProcessor | None:
        for processor in self.processors:
            if processor.supports(path):
                return processor
        return None


def default_registry() -> ProcessorRegistry:
    registry = ProcessorRegistry()

    # Source first because files like CMakeLists.txt and .txt-like build files
    # can otherwise be swallowed by the document processor.
    registry.register(SourceCodeProcessor())
    registry.register(DocumentProcessor())

    return registry

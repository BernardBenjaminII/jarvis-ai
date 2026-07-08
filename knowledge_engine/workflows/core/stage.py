from __future__ import annotations

from abc import ABC, abstractmethod

from .context import KnowledgeContext


class WorkflowStage(ABC):
    name = "Unnamed Stage"

    @abstractmethod
    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        raise NotImplementedError

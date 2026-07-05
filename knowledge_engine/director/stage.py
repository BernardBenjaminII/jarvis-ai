from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StageResult:

    name: str

    success: bool = True

    metrics: dict = field(default_factory=dict)

    warnings: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)

    elapsed: float = 0.0


class AssimilationStage(ABC):

    name = "Unnamed Stage"

    order = 0

    @abstractmethod
    def run(self, context) -> StageResult:
        ...

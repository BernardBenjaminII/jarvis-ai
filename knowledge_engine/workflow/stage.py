from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkflowContext:
    root: Path
    database: Any
    runtime: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    name: str
    success: bool = True
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed: float = 0.0


class WorkflowStage(ABC):
    name: str = "unnamed"
    order: int = 1000
    requires: set[str] = set()
    provides: set[str] = set()

    @abstractmethod
    def run(self, context: WorkflowContext) -> WorkflowResult:
        ...

from __future__ import annotations

from typing import Callable

from knowledge_engine.workflow.registry import WorkflowRegistry
from knowledge_engine.workflow.smoke import build_smoke_registry


_BUILDERS: dict[str, Callable[[], WorkflowRegistry]] = {
    "smoke": build_smoke_registry,
}


def register(name: str, builder: Callable[[], WorkflowRegistry]) -> None:
    _BUILDERS[name] = builder


def available() -> list[str]:
    return sorted(_BUILDERS.keys())


def build(name: str) -> WorkflowRegistry:
    try:
        return _BUILDERS[name]()
    except KeyError:
        raise ValueError(f"Unknown workflow '{name}'")

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionPlan:
    """
    Represents a single executable step chosen by the planner.
    """

    type: str                 # tool | llm | agent
    tool: str | None = None
    action: str | None = None
    args: dict[str, Any] = field(default_factory=dict)

    model: str | None = None
    prompt: str | None = None

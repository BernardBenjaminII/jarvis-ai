from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionPlan:
    """
    Describes one unit of work for JARVIS.

    type:
        tool    -> execute a registered tool
        llm     -> query an LLM
        agent   -> invoke an agent
        pipeline-> execute multiple plans
    """

    type: str

    tool: str = ""
    action: str = ""

    args: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AssimilationContext:
    """
    Shared runtime context passed to every assimilation stage.
    """

    root: Path
    database: Any

    runtime: dict[str, Any] = field(default_factory=dict)

    metrics: dict[str, Any] = field(default_factory=dict)

    artifacts: dict[str, Any] = field(default_factory=dict)

    warnings: list[str] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)

    cancelled: bool = False

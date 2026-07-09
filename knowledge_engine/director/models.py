from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DirectorRequest:
    intent: str
    source_path: Path | None = None
    query: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DirectorResponse:
    intent: str
    workflow: str
    passed: bool
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

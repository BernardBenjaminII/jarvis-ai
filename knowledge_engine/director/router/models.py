from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RoutedIntent:
    intent: str
    confidence: float
    reason: str
    source_path: Path | None = None
    query: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResourceGuess:
    object_path: Path
    object_name: str
    object_type_hint: str | None
    primary_file_path: str | None
    confidence: float
    reason: str

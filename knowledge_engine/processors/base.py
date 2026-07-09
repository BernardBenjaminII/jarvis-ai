from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ProcessorResult:
    file_path: str
    processor: str
    content_type: str
    text: str
    metadata: dict = field(default_factory=dict)
    status: str = "processed"
    error: str | None = None


class BaseProcessor:
    name = "base_processor"
    content_type = "unknown"
    extensions: set[str] = set()
    filenames: set[str] = set()

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions or path.name in self.filenames

    def process(self, path: Path) -> ProcessorResult:
        raise NotImplementedError

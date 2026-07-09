from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeContext:
    source_path: Path

    content_type: str = ""
    raw_text: str = ""
    extracted_text: str = ""

    processor: str = ""
    processor_status: str = ""

    chunk_strategy: str = ""

    embedding_model: str = ""
    embedding_count: int = 0

    registry_count: int = 0
    retrieval_verified: bool = False
    retrieval_service: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[str] = field(default_factory=list)
    embeddings: list[Any] = field(default_factory=list)
    objects: list[Any] = field(default_factory=list)
    registry_ids: list[Any] = field(default_factory=list)
    graph_nodes: list[Any] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

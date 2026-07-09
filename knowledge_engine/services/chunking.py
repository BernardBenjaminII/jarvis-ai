from __future__ import annotations

from knowledge_engine.chunking.chunker import (
    DocumentChunker,
    ChunkingResult,
)


class ChunkingService:
    """
    Canonical public API for document chunking.

    All workflows, Doctor checks, CLI tools, Librarian,
    and future agents should use this service.
    """

    def __init__(self):
        self.chunker = DocumentChunker()

    def chunk(
        self,
        text: str,
        *,
        file_path: str | None = None,
    ) -> ChunkingResult:
        return self.chunker.chunk(
            text=text,
            file_path=file_path,
        )

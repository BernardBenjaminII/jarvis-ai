from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    chunk_uuid: str
    file_path: str
    chunk_index: int
    chunk_type: str
    heading: str | None
    text: str
    char_count: int
    checksum: str
    embedding_state: str = "not_embedded"

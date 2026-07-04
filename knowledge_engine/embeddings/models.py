from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkEmbedding:
    chunk_uuid: str
    provider: str
    model: str
    dimensions: int
    vector: list[float]

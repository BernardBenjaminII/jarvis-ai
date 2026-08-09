from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True, slots=True)
class QueryAnalysis:
    raw: str
    terms: tuple[str, ...]
    quoted_phrases: tuple[str, ...]
    entities: tuple[str, ...]
    normalized: str
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class Candidate:
    document_id: str
    chunk_id: str
    title: str
    file_path: str
    excerpt: str
    bm25_rank: float | None = None
    lexical_rank_position: int | None = None
    semantic_score: float | None = None
    semantic_rank_position: int | None = None
    metadata_score: float = 0.0
    fused_score: float = 0.0
    provenance_score: float = 0.0
    duplicate_key: str = ""
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

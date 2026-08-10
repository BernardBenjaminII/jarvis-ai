from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class SemanticCandidate:
    rank: int
    score: float
    source: str
    runtime_chunk_id: int
    runtime_document_id: int
    chunk_uuid: str
    fragment_uuid: Optional[str]
    fragment_index: Optional[int]
    document_title: str
    file_path: str
    text_preview: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SemanticSearchResult:
    query: str
    provider: str
    model: str
    dimensions: int
    scope: str
    scanned_canonical: int
    scanned_fragments: int
    candidates: tuple[SemanticCandidate, ...]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "provider": self.provider,
            "model": self.model,
            "dimensions": self.dimensions,
            "scope": self.scope,
            "scanned_canonical": self.scanned_canonical,
            "scanned_fragments": self.scanned_fragments,
            "candidate_count": len(self.candidates),
            "candidates": [c.to_dict() for c in self.candidates],
        }

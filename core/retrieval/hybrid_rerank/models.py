from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class HybridCandidate:
    rank: int
    hybrid_score: float
    semantic_score: float
    lexical_score: float
    title_score: float
    diversity_penalty: float
    duplicate_key: str
    source: str
    runtime_chunk_id: int
    runtime_document_id: int
    chunk_uuid: str
    fragment_uuid: str | None
    fragment_index: int | None
    document_title: str
    file_path: str
    text_preview: str
    matched_terms: tuple[str, ...]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["matched_terms"] = list(self.matched_terms)
        return d


@dataclass(frozen=True)
class HybridSearchResult:
    query: str
    query_terms: tuple[str, ...]
    raw_candidate_count: int
    deduplicated_candidate_count: int
    final_candidate_count: int
    candidates: tuple[HybridCandidate, ...]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "query_terms": list(self.query_terms),
            "raw_candidate_count": self.raw_candidate_count,
            "deduplicated_candidate_count": self.deduplicated_candidate_count,
            "final_candidate_count": self.final_candidate_count,
            "candidates": [c.to_dict() for c in self.candidates],
        }

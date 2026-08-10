from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    rank: int
    source_role: str
    runtime_chunk_id: int
    runtime_document_id: int
    document_title: str
    file_path: str
    chunk_uuid: str
    fragment_uuid: str | None
    hybrid_score: float
    semantic_score: float
    lexical_score: float
    title_score: float
    matched_terms: tuple[str, ...]
    text: str
    chars: int

    def to_dict(self) -> dict:
        d = asdict(self)
        d["matched_terms"] = list(self.matched_terms)
        return d


@dataclass(frozen=True)
class EvidenceBundle:
    query: str
    query_terms: tuple[str, ...]
    accepted_candidates: int
    rejected_candidates: int
    expanded_neighbors: int
    selected_evidence: tuple[EvidenceItem, ...]
    total_chars: int
    max_chars: int

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "query_terms": list(self.query_terms),
            "accepted_candidates": self.accepted_candidates,
            "rejected_candidates": self.rejected_candidates,
            "expanded_neighbors": self.expanded_neighbors,
            "selected_evidence_count": len(self.selected_evidence),
            "total_chars": self.total_chars,
            "max_chars": self.max_chars,
            "selected_evidence": [e.to_dict() for e in self.selected_evidence],
        }

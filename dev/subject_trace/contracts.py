from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CandidateSubjectTrace:
    candidate_id: str
    title: str
    source_path: str
    query_subjects: tuple[str, ...]
    candidate_subjects: tuple[str, ...]
    candidate_domain: str
    aliases_considered: tuple[str, ...]
    exact_matches: tuple[str, ...]
    alias_matches: tuple[str, ...]
    overlap_score: float
    subject_score: float | None
    final_score: float | None
    threshold: float | None
    decision: str
    diagnosis: str
    missing_metadata: bool
    taxonomy_mismatch: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "source_path": self.source_path,
            "query_subjects": list(self.query_subjects),
            "candidate_subjects": list(self.candidate_subjects),
            "candidate_domain": self.candidate_domain,
            "aliases_considered": list(self.aliases_considered),
            "exact_matches": list(self.exact_matches),
            "alias_matches": list(self.alias_matches),
            "overlap_score": self.overlap_score,
            "subject_score": self.subject_score,
            "final_score": self.final_score,
            "threshold": self.threshold,
            "decision": self.decision,
            "diagnosis": self.diagnosis,
            "missing_metadata": self.missing_metadata,
            "taxonomy_mismatch": self.taxonomy_mismatch,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProbeSubjectTrace:
    probe_id: str
    query: str
    expected_subjects: tuple[str, ...]
    normalized_query: str
    query_tokens: tuple[str, ...]
    detected_subjects: tuple[str, ...]
    raw_count: int
    qualified_count: int
    candidates: tuple[CandidateSubjectTrace, ...]
    dominant_diagnosis: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "query": self.query,
            "expected_subjects": list(self.expected_subjects),
            "normalized_query": self.normalized_query,
            "query_tokens": list(self.query_tokens),
            "detected_subjects": list(self.detected_subjects),
            "raw_count": self.raw_count,
            "qualified_count": self.qualified_count,
            "candidates": [item.to_dict() for item in self.candidates],
            "dominant_diagnosis": self.dominant_diagnosis,
        }


@dataclass(frozen=True, slots=True)
class SubjectTraceReport:
    status: str
    classification: str
    probes: tuple[ProbeSubjectTrace, ...]
    summary: dict[str, Any]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "classification": self.classification,
            "probes": [item.to_dict() for item in self.probes],
            "summary": dict(self.summary),
            "recommendations": list(self.recommendations),
        }

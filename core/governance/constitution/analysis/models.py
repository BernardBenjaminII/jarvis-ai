from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .contracts import ANALYSIS_SCHEMA_VERSION


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    source_path: str
    text: str
    modality: str
    domain: str
    line_start: int
    line_end: int
    repository_id: str
    source_hash: str
    excerpt_hash: str
    authority: str
    authority_rank: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Relationship:
    relationship_id: str
    source_claim_id: str
    target_claim_id: str
    relationship_type: str
    score: float
    rationale: str
    authority_resolution: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisStatistics:
    claims: int
    relationships: int
    duplicates: int
    supports: int
    contradictions: int
    refines: int
    authority_resolutions: int
    diagnostics: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConstitutionalAnalysis:
    schema_version: str
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    claims: tuple[ClaimRecord, ...]
    relationships: tuple[Relationship, ...]
    statistics: AnalysisStatistics
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_fingerprint": self.repository_fingerprint,
            "extraction_fingerprint": self.extraction_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
            "claims": [item.to_dict() for item in self.claims],
            "relationships": [item.to_dict() for item in self.relationships],
            "statistics": self.statistics.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

    @classmethod
    def empty(cls, repository_fingerprint: str, extraction_fingerprint: str) -> "ConstitutionalAnalysis":
        return cls(
            schema_version=ANALYSIS_SCHEMA_VERSION,
            repository_fingerprint=repository_fingerprint,
            extraction_fingerprint=extraction_fingerprint,
            analysis_fingerprint="",
            claims=(),
            relationships=(),
            statistics=AnalysisStatistics(0, 0, 0, 0, 0, 0, 0, 0),
            diagnostics=(),
        )

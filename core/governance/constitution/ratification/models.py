from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class RatificationPolicy:
    minimum_supporting_claims: int = 1
    allow_unresolved_conflicts: bool = False
    ratify_singleton_high_authority: bool = True
    high_authority_threshold: int = 600
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    source_path: str
    text: str
    domain: str
    authority: str
    authority_rank: int
    source_hash: str
    excerpt_hash: str
    line_start: int
    line_end: int
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class ConstitutionalArticle:
    article_id: str
    title: str
    canonical_text: str
    domain: str
    section_id: str
    status: str
    authority: str
    authority_rank: int
    supporting_claim_ids: tuple[str, ...]
    supporting_source_paths: tuple[str, ...]
    conflict_claim_ids: tuple[str, ...]
    evidence_count: int
    fingerprint: str
    revision: int
    rationale: str
    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["supporting_claim_ids"] = list(self.supporting_claim_ids)
        value["supporting_source_paths"] = list(self.supporting_source_paths)
        value["conflict_claim_ids"] = list(self.conflict_claim_ids)
        return value

@dataclass(frozen=True)
class ConstitutionalSection:
    section_id: str
    title: str
    domain: str
    article_ids: tuple[str, ...]
    fingerprint: str
    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["article_ids"] = list(self.article_ids)
        return value

@dataclass(frozen=True)
class TraceabilityRecord:
    article_id: str
    claim_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    source_hashes: tuple[str, ...]
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["claim_ids"] = list(self.claim_ids)
        value["source_paths"] = list(self.source_paths)
        value["source_hashes"] = list(self.source_hashes)
        return value

@dataclass(frozen=True)
class RatificationStatistics:
    claims: int
    clusters: int
    articles: int
    ratified_articles: int
    review_required_articles: int
    rejected_articles: int
    sections: int
    traced_claims: int
    unrepresented_claims: int
    diagnostics: int
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class CanonicalConstitution:
    schema_version: str
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    ratification_fingerprint: str
    policy: RatificationPolicy
    articles: tuple[ConstitutionalArticle, ...]
    sections: tuple[ConstitutionalSection, ...]
    traceability: tuple[TraceabilityRecord, ...]
    statistics: RatificationStatistics
    diagnostics: tuple[str, ...]
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_fingerprint": self.repository_fingerprint,
            "extraction_fingerprint": self.extraction_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
            "ratification_fingerprint": self.ratification_fingerprint,
            "policy": self.policy.to_dict(),
            "articles": [x.to_dict() for x in self.articles],
            "sections": [x.to_dict() for x in self.sections],
            "traceability": [x.to_dict() for x in self.traceability],
            "statistics": self.statistics.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

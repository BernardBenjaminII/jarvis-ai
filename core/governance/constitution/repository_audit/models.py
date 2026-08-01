from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RepositoryAuditPolicy:
    included_suffixes: tuple[str, ...]
    excluded_directories: tuple[str, ...]
    maximum_file_bytes: int = 2_000_000
    include_source_code: bool = False
    minimum_match_score: float = 0.35
    contradiction_threshold: float = 0.72

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["included_suffixes"] = list(self.included_suffixes)
        value["excluded_directories"] = list(self.excluded_directories)
        return value


@dataclass(frozen=True)
class RepositoryArtifact:
    artifact_id: str
    path: str
    artifact_type: str
    suffix: str
    size_bytes: int
    content_fingerprint: str
    content: str
    domain: str

    def to_dict(self, include_content: bool = False) -> dict[str, Any]:
        value = asdict(self)
        if not include_content:
            value.pop("content", None)
        return value


@dataclass(frozen=True)
class RepositoryArtifactAssessment:
    artifact_id: str
    path: str
    overall_status: str
    applicable_articles: tuple[str, ...]
    finding_ids: tuple[str, ...]
    assessment_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["applicable_articles"] = list(self.applicable_articles)
        value["finding_ids"] = list(self.finding_ids)
        return value


@dataclass(frozen=True)
class ArticleUsage:
    article_id: str
    reference_count: int
    compliant_count: int
    review_required_count: int
    noncompliant_count: int
    artifact_ids: tuple[str, ...]
    usage_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["artifact_ids"] = list(self.artifact_ids)
        return value


@dataclass(frozen=True)
class RepositoryAuditStatistics:
    artifacts_discovered: int
    artifacts_evaluated: int
    findings: int
    applicable_artifacts: int
    compliant_artifacts: int
    review_required_artifacts: int
    noncompliant_artifacts: int
    not_applicable_artifacts: int
    articles_considered: int
    articles_referenced: int
    articles_unused: int
    diagnostics: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepositoryAuditAssessment:
    schema_version: str
    repository_root: str
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    ratification_fingerprint: str
    compliance_fingerprint: str
    certification_fingerprint: str
    audit_fingerprint: str
    policy: RepositoryAuditPolicy
    artifacts: tuple[RepositoryArtifact, ...]
    assessments: tuple[RepositoryArtifactAssessment, ...]
    findings: tuple[dict[str, Any], ...]
    article_usage: tuple[ArticleUsage, ...]
    statistics: RepositoryAuditStatistics
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_root": self.repository_root,
            "repository_fingerprint": self.repository_fingerprint,
            "extraction_fingerprint": self.extraction_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
            "ratification_fingerprint": self.ratification_fingerprint,
            "compliance_fingerprint": self.compliance_fingerprint,
            "certification_fingerprint": self.certification_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "policy": self.policy.to_dict(),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "assessments": [item.to_dict() for item in self.assessments],
            "findings": list(self.findings),
            "article_usage": [item.to_dict() for item in self.article_usage],
            "statistics": self.statistics.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

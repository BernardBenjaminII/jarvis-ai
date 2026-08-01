from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CompliancePolicy:
    minimum_match_score: float = 0.35
    contradiction_threshold: float = 0.72
    require_ratified_articles_only: bool = True
    fail_on_unresolved_article: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChangeSubject:
    subject_id: str
    subject_type: str
    path: str
    title: str
    content: str
    domain: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArticleReference:
    article_id: str
    canonical_text: str
    domain: str
    status: str
    authority: str
    authority_rank: int
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceFinding:
    finding_id: str
    subject_id: str
    article_id: str
    status: str
    severity: str
    score: float
    rationale: str
    subject_excerpt: str
    article_excerpt: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubjectAssessment:
    subject_id: str
    overall_status: str
    applicable_articles: tuple[str, ...]
    finding_ids: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["applicable_articles"] = list(self.applicable_articles)
        value["finding_ids"] = list(self.finding_ids)
        return value


@dataclass(frozen=True)
class ComplianceStatistics:
    subjects: int
    articles_considered: int
    findings: int
    compliant_findings: int
    review_required_findings: int
    noncompliant_findings: int
    not_applicable_findings: int
    compliant_subjects: int
    review_required_subjects: int
    noncompliant_subjects: int
    diagnostics: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComplianceAssessment:
    schema_version: str
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    ratification_fingerprint: str
    compliance_fingerprint: str
    policy: CompliancePolicy
    subjects: tuple[ChangeSubject, ...]
    articles: tuple[ArticleReference, ...]
    findings: tuple[ComplianceFinding, ...]
    assessments: tuple[SubjectAssessment, ...]
    statistics: ComplianceStatistics
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_fingerprint": self.repository_fingerprint,
            "extraction_fingerprint": self.extraction_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
            "ratification_fingerprint": self.ratification_fingerprint,
            "compliance_fingerprint": self.compliance_fingerprint,
            "policy": self.policy.to_dict(),
            "subjects": [item.to_dict() for item in self.subjects],
            "articles": [item.to_dict() for item in self.articles],
            "findings": [item.to_dict() for item in self.findings],
            "assessments": [item.to_dict() for item in self.assessments],
            "statistics": self.statistics.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

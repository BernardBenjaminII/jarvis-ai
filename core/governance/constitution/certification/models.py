from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CertificationPolicy:
    minimum_positive_findings: int = 1
    minimum_negative_findings: int = 1
    minimum_review_findings: int = 1
    minimum_not_applicable_subjects: int = 1
    require_rank_one_match: bool = True
    require_complete_traceability: bool = True
    require_determinism: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificationScenario:
    scenario_id: str
    kind: str
    title: str
    description: str
    expected_status: str
    expected_article_id: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiveCertificationScenario:
    scenario_id: str
    kind: str
    title: str
    expected_status: str
    expected_article_id: str
    subject_id: str
    subject_title: str
    subject_content: str
    subject_domain: str
    source_article_fingerprint: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    status: str
    observed_status: str
    observed_article_id: str
    rank: int
    findings: int
    traceability_complete: bool
    rationale: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificationStatistics:
    scenarios: int
    passed: int
    failed: int
    skipped: int
    positive_findings: int
    negative_findings: int
    review_findings: int
    not_applicable_subjects: int
    diagnostics: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificationAssessment:
    schema_version: str
    repository_fingerprint: str
    extraction_fingerprint: str
    analysis_fingerprint: str
    ratification_fingerprint: str
    compliance_fingerprint: str
    certification_fingerprint: str
    policy: CertificationPolicy
    scenarios: tuple[CertificationScenario | LiveCertificationScenario, ...]
    results: tuple[ScenarioResult, ...]
    statistics: CertificationStatistics
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository_fingerprint": self.repository_fingerprint,
            "extraction_fingerprint": self.extraction_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
            "ratification_fingerprint": self.ratification_fingerprint,
            "compliance_fingerprint": self.compliance_fingerprint,
            "certification_fingerprint": self.certification_fingerprint,
            "policy": self.policy.to_dict(),
            "scenarios": [item.to_dict() for item in self.scenarios],
            "results": [item.to_dict() for item in self.results],
            "statistics": self.statistics.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

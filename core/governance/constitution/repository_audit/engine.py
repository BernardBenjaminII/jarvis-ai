from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .contracts import REPOSITORY_AUDIT_SCHEMA_VERSION
from .discovery import discover_repository_artifacts
from .evaluator import evaluate_repository_artifacts
from .fingerprints import canonical_fingerprint
from .models import (
    RepositoryArtifactAssessment,
    RepositoryAuditAssessment,
    RepositoryAuditPolicy,
    RepositoryAuditStatistics,
)
from .policies import default_repository_audit_policy
from .statistics import build_article_usage


class RepositoryConstitutionalAuditEngine:
    def assess(
        self,
        *,
        repository_root: Path,
        ratification_directory: Path,
        compliance_fingerprint: str,
        certification_fingerprint: str,
        policy: RepositoryAuditPolicy | None = None,
    ) -> RepositoryAuditAssessment:
        active_policy = policy or default_repository_audit_policy()
        artifacts = discover_repository_artifacts(repository_root, active_policy)
        if not artifacts:
            raise RuntimeError("Repository audit discovered no eligible artifacts.")

        compliance = evaluate_repository_artifacts(
            artifacts=artifacts,
            ratification_directory=ratification_directory,
            policy=active_policy,
        )

        path_by_id = {item.artifact_id: item.path for item in artifacts}
        assessments = tuple(
            RepositoryArtifactAssessment(
                artifact_id=item.subject_id,
                path=path_by_id[item.subject_id],
                overall_status=item.overall_status,
                applicable_articles=item.applicable_articles,
                finding_ids=item.finding_ids,
                assessment_fingerprint=item.fingerprint,
            )
            for item in compliance.assessments
        )

        findings = tuple(item.to_dict() for item in compliance.findings)
        article_usage = build_article_usage(
            article_ids=tuple(item.article_id for item in compliance.articles),
            findings=findings,
        )

        status_counts = defaultdict(int)
        for item in assessments:
            status_counts[item.overall_status] += 1

        referenced = sum(1 for item in article_usage if item.reference_count > 0)
        statistics = RepositoryAuditStatistics(
            artifacts_discovered=len(artifacts),
            artifacts_evaluated=len(assessments),
            findings=len(findings),
            applicable_artifacts=(
                len(assessments) - status_counts["not_applicable"]
            ),
            compliant_artifacts=status_counts["compliant"],
            review_required_artifacts=status_counts["review_required"],
            noncompliant_artifacts=status_counts["noncompliant"],
            not_applicable_artifacts=status_counts["not_applicable"],
            articles_considered=len(compliance.articles),
            articles_referenced=referenced,
            articles_unused=len(compliance.articles) - referenced,
            diagnostics=len(compliance.diagnostics),
        )

        diagnostics = list(compliance.diagnostics)
        if statistics.artifacts_discovered != statistics.artifacts_evaluated:
            diagnostics.append(
                "Not every discovered repository artifact received an assessment."
            )
        if len({item.artifact_id for item in artifacts}) != len(artifacts):
            diagnostics.append("Duplicate repository artifact identifiers detected.")
        if len({item["finding_id"] for item in findings}) != len(findings):
            diagnostics.append("Duplicate repository audit finding identifiers detected.")

        basis = {
            "schema_version": REPOSITORY_AUDIT_SCHEMA_VERSION,
            "repository_root": str(repository_root.resolve()),
            "repository_fingerprint": compliance.repository_fingerprint,
            "extraction_fingerprint": compliance.extraction_fingerprint,
            "analysis_fingerprint": compliance.analysis_fingerprint,
            "ratification_fingerprint": compliance.ratification_fingerprint,
            "compliance_fingerprint": compliance_fingerprint,
            "certification_fingerprint": certification_fingerprint,
            "policy": active_policy.to_dict(),
            "artifacts": [item.to_dict() for item in artifacts],
            "assessments": [item.to_dict() for item in assessments],
            "findings": list(findings),
            "article_usage": [item.to_dict() for item in article_usage],
            "statistics": statistics.to_dict(),
            "diagnostics": diagnostics,
        }

        return RepositoryAuditAssessment(
            schema_version=REPOSITORY_AUDIT_SCHEMA_VERSION,
            repository_root=str(repository_root.resolve()),
            repository_fingerprint=compliance.repository_fingerprint,
            extraction_fingerprint=compliance.extraction_fingerprint,
            analysis_fingerprint=compliance.analysis_fingerprint,
            ratification_fingerprint=compliance.ratification_fingerprint,
            compliance_fingerprint=compliance_fingerprint,
            certification_fingerprint=certification_fingerprint,
            audit_fingerprint=canonical_fingerprint(basis),
            policy=active_policy,
            artifacts=artifacts,
            assessments=assessments,
            findings=findings,
            article_usage=article_usage,
            statistics=statistics,
            diagnostics=tuple(diagnostics),
        )

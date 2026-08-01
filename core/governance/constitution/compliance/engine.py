from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .contracts import COMPLIANCE_SCHEMA_VERSION, ComplianceStatus
from .evaluator import evaluate_pair
from .loader import load_ratification, load_subjects
from .models import (
    ComplianceAssessment,
    CompliancePolicy,
    ComplianceStatistics,
    SubjectAssessment,
)


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class ConstitutionalComplianceEngine:
    def assess(
        self,
        ratification_directory: Path,
        subject_path: Path,
        policy: CompliancePolicy | None = None,
    ) -> ComplianceAssessment:
        active_policy = policy or CompliancePolicy()
        (
            repository_fingerprint,
            extraction_fingerprint,
            analysis_fingerprint,
            ratification_fingerprint,
            articles,
        ) = load_ratification(
            ratification_directory,
            require_ratified_only=active_policy.require_ratified_articles_only,
        )
        subjects = load_subjects(subject_path)

        findings = []
        for subject in subjects:
            for article in articles:
                finding = evaluate_pair(subject, article, active_policy)
                if finding is not None:
                    findings.append(finding)

        findings.sort(
            key=lambda item: (
                item.subject_id,
                item.article_id,
                item.status,
                item.finding_id,
            )
        )

        findings_by_subject: dict[str, list] = defaultdict(list)
        for finding in findings:
            findings_by_subject[finding.subject_id].append(finding)

        assessments = []
        for subject in subjects:
            applicable = findings_by_subject.get(subject.subject_id, [])
            statuses = {item.status for item in applicable}
            if ComplianceStatus.NONCOMPLIANT.value in statuses:
                overall = ComplianceStatus.NONCOMPLIANT.value
            elif ComplianceStatus.REVIEW_REQUIRED.value in statuses:
                overall = ComplianceStatus.REVIEW_REQUIRED.value
            elif ComplianceStatus.COMPLIANT.value in statuses:
                overall = ComplianceStatus.COMPLIANT.value
            else:
                overall = ComplianceStatus.NOT_APPLICABLE.value

            basis = {
                "subject_id": subject.subject_id,
                "overall_status": overall,
                "applicable_articles": sorted({item.article_id for item in applicable}),
                "finding_ids": [item.finding_id for item in applicable],
            }
            assessments.append(
                SubjectAssessment(
                    subject_id=subject.subject_id,
                    overall_status=overall,
                    applicable_articles=tuple(basis["applicable_articles"]),
                    finding_ids=tuple(basis["finding_ids"]),
                    fingerprint=_hash(basis),
                )
            )

        assessments.sort(key=lambda item: item.subject_id)

        status_counts = defaultdict(int)
        for finding in findings:
            status_counts[finding.status] += 1

        subject_status_counts = defaultdict(int)
        for assessment in assessments:
            subject_status_counts[assessment.overall_status] += 1

        statistics = ComplianceStatistics(
            subjects=len(subjects),
            articles_considered=len(articles),
            findings=len(findings),
            compliant_findings=status_counts[ComplianceStatus.COMPLIANT.value],
            review_required_findings=status_counts[ComplianceStatus.REVIEW_REQUIRED.value],
            noncompliant_findings=status_counts[ComplianceStatus.NONCOMPLIANT.value],
            not_applicable_findings=status_counts[ComplianceStatus.NOT_APPLICABLE.value],
            compliant_subjects=subject_status_counts[ComplianceStatus.COMPLIANT.value],
            review_required_subjects=subject_status_counts[ComplianceStatus.REVIEW_REQUIRED.value],
            noncompliant_subjects=subject_status_counts[ComplianceStatus.NONCOMPLIANT.value],
            diagnostics=0,
        )

        basis = {
            "schema_version": COMPLIANCE_SCHEMA_VERSION,
            "repository_fingerprint": repository_fingerprint,
            "extraction_fingerprint": extraction_fingerprint,
            "analysis_fingerprint": analysis_fingerprint,
            "ratification_fingerprint": ratification_fingerprint,
            "policy": active_policy.to_dict(),
            "subjects": [item.to_dict() for item in subjects],
            "articles": [item.to_dict() for item in articles],
            "findings": [item.to_dict() for item in findings],
            "assessments": [item.to_dict() for item in assessments],
            "statistics": statistics.to_dict(),
        }

        return ComplianceAssessment(
            schema_version=COMPLIANCE_SCHEMA_VERSION,
            repository_fingerprint=repository_fingerprint,
            extraction_fingerprint=extraction_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            ratification_fingerprint=ratification_fingerprint,
            compliance_fingerprint=_hash(basis),
            policy=active_policy,
            subjects=subjects,
            articles=articles,
            findings=tuple(findings),
            assessments=tuple(assessments),
            statistics=statistics,
            diagnostics=(),
        )

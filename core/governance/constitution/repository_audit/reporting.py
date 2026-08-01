from __future__ import annotations

import json
from pathlib import Path

from .models import RepositoryAuditAssessment


class RepositoryConstitutionalAuditReporter:
    def write(
        self,
        assessment: RepositoryAuditAssessment,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        artifacts = {
            "constitutional_repository_inventory.json": {
                "schema_version": assessment.schema_version,
                "audit_fingerprint": assessment.audit_fingerprint,
                "artifacts": [item.to_dict() for item in assessment.artifacts],
            },
            "constitutional_repository_audit.json": assessment.to_dict(),
            "constitutional_repository_statistics.json": {
                "schema_version": assessment.schema_version,
                "audit_fingerprint": assessment.audit_fingerprint,
                "statistics": assessment.statistics.to_dict(),
            },
            "constitutional_article_usage.json": {
                "schema_version": assessment.schema_version,
                "audit_fingerprint": assessment.audit_fingerprint,
                "article_usage": [
                    item.to_dict() for item in assessment.article_usage
                ],
            },
            "constitutional_article_heatmap.json": {
                "schema_version": assessment.schema_version,
                "audit_fingerprint": assessment.audit_fingerprint,
                "most_referenced": [
                    item.to_dict()
                    for item in sorted(
                        assessment.article_usage,
                        key=lambda value: (
                            -value.reference_count,
                            value.article_id,
                        ),
                    )[:25]
                ],
                "most_noncompliant": [
                    item.to_dict()
                    for item in sorted(
                        assessment.article_usage,
                        key=lambda value: (
                            -value.noncompliant_count,
                            -value.review_required_count,
                            value.article_id,
                        ),
                    )[:25]
                ],
                "unused_articles": [
                    item.article_id
                    for item in assessment.article_usage
                    if item.reference_count == 0
                ],
            },
            "constitutional_repository_traceability.json": {
                "repository_fingerprint": assessment.repository_fingerprint,
                "extraction_fingerprint": assessment.extraction_fingerprint,
                "analysis_fingerprint": assessment.analysis_fingerprint,
                "ratification_fingerprint": assessment.ratification_fingerprint,
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "certification_fingerprint": assessment.certification_fingerprint,
                "audit_fingerprint": assessment.audit_fingerprint,
                "artifact_fingerprints": {
                    item.artifact_id: item.content_fingerprint
                    for item in assessment.artifacts
                },
                "assessment_fingerprints": {
                    item.artifact_id: item.assessment_fingerprint
                    for item in assessment.assessments
                },
            },
            "constitutional_repository_findings.json": {
                "schema_version": assessment.schema_version,
                "audit_fingerprint": assessment.audit_fingerprint,
                "findings": list(assessment.findings),
            },
        }

        written = []
        for name, payload in artifacts.items():
            path = output_directory / name
            path.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            written.append(path)

        s = assessment.statistics
        report = output_directory / "constitutional_repository_report.md"
        report.write_text(
            "\n".join(
                [
                    "# Genesis VII-C4.2 Repository-Wide Constitutional Audit",
                    "",
                    f"**Audit fingerprint:** `{assessment.audit_fingerprint}`",
                    "",
                    "## Fingerprint chain",
                    "",
                    f"- Repository: `{assessment.repository_fingerprint}`",
                    f"- Extraction: `{assessment.extraction_fingerprint}`",
                    f"- Analysis: `{assessment.analysis_fingerprint}`",
                    f"- Ratification: `{assessment.ratification_fingerprint}`",
                    f"- Compliance: `{assessment.compliance_fingerprint}`",
                    f"- Certification: `{assessment.certification_fingerprint}`",
                    "",
                    "## Repository constitutional health",
                    "",
                    f"- Artifacts discovered: {s.artifacts_discovered}",
                    f"- Artifacts evaluated: {s.artifacts_evaluated}",
                    f"- Applicable artifacts: {s.applicable_artifacts}",
                    f"- Compliant artifacts: {s.compliant_artifacts}",
                    f"- Review required: {s.review_required_artifacts}",
                    f"- Noncompliant artifacts: {s.noncompliant_artifacts}",
                    f"- Not applicable: {s.not_applicable_artifacts}",
                    f"- Findings: {s.findings}",
                    f"- Articles considered: {s.articles_considered}",
                    f"- Articles referenced: {s.articles_referenced}",
                    f"- Articles unused: {s.articles_unused}",
                    f"- Diagnostics: {len(assessment.diagnostics)}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)

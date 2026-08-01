from __future__ import annotations

import json
from pathlib import Path

from .models import ComplianceAssessment


class ConstitutionalComplianceReporter:
    def write(
        self,
        assessment: ComplianceAssessment,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        summary = assessment.to_dict()
        summary.pop("subjects")
        summary.pop("articles")
        summary.pop("findings")
        summary.pop("assessments")

        artifacts = {
            "constitutional_compliance.json": summary,
            "constitutional_compliance_subjects.json": {
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "subjects": [item.to_dict() for item in assessment.subjects],
            },
            "constitutional_compliance_findings.json": {
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "findings": [item.to_dict() for item in assessment.findings],
            },
            "constitutional_compliance_assessments.json": {
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "assessments": [item.to_dict() for item in assessment.assessments],
            },
            "constitutional_compliance_traceability.json": {
                "repository_fingerprint": assessment.repository_fingerprint,
                "extraction_fingerprint": assessment.extraction_fingerprint,
                "analysis_fingerprint": assessment.analysis_fingerprint,
                "ratification_fingerprint": assessment.ratification_fingerprint,
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "article_fingerprints": {
                    article.article_id: article.fingerprint
                    for article in assessment.articles
                },
                "subject_fingerprints": {
                    subject.subject_id: subject.fingerprint
                    for subject in assessment.subjects
                },
            },
        }

        written = []
        for name, payload in artifacts.items():
            path = output_directory / name
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            written.append(path)

        report = output_directory / "constitutional_compliance_report.md"
        s = assessment.statistics
        report.write_text(
            "\n".join(
                [
                    "# Genesis VII-C4 Constitutional Compliance Report",
                    "",
                    f"**Repository fingerprint:** `{assessment.repository_fingerprint}`",
                    f"**Extraction fingerprint:** `{assessment.extraction_fingerprint}`",
                    f"**Analysis fingerprint:** `{assessment.analysis_fingerprint}`",
                    f"**Ratification fingerprint:** `{assessment.ratification_fingerprint}`",
                    f"**Compliance fingerprint:** `{assessment.compliance_fingerprint}`",
                    "",
                    "## Statistics",
                    "",
                    f"- Subjects: {s.subjects}",
                    f"- Articles considered: {s.articles_considered}",
                    f"- Findings: {s.findings}",
                    f"- Compliant findings: {s.compliant_findings}",
                    f"- Review-required findings: {s.review_required_findings}",
                    f"- Noncompliant findings: {s.noncompliant_findings}",
                    f"- Compliant subjects: {s.compliant_subjects}",
                    f"- Review-required subjects: {s.review_required_subjects}",
                    f"- Noncompliant subjects: {s.noncompliant_subjects}",
                    f"- Diagnostics: {s.diagnostics}",
                    "",
                    "## Governance boundary",
                    "",
                    "C4 performs deterministic candidate compliance analysis.",
                    "It does not replace Commander judgment, legal review, security review,",
                    "or formal constitutional adjudication.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)

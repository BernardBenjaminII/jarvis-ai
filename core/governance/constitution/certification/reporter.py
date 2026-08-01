from __future__ import annotations

import json
from pathlib import Path

from .models import CertificationAssessment


class ConstitutionalCertificationReporter:
    def write(
        self,
        assessment: CertificationAssessment,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)

        artifacts = {
            "constitutional_certification.json": assessment.to_dict(),
            "constitutional_certification_policy.json": {
                "schema_version": assessment.schema_version,
                "certification_fingerprint": assessment.certification_fingerprint,
                "policy": assessment.policy.to_dict(),
            },
            "constitutional_certification_traceability.json": {
                "repository_fingerprint": assessment.repository_fingerprint,
                "extraction_fingerprint": assessment.extraction_fingerprint,
                "analysis_fingerprint": assessment.analysis_fingerprint,
                "ratification_fingerprint": assessment.ratification_fingerprint,
                "compliance_fingerprint": assessment.compliance_fingerprint,
                "certification_fingerprint": assessment.certification_fingerprint,
                "scenario_fingerprints": {
                    item.scenario_id: item.fingerprint
                    for item in assessment.scenarios
                },
                "result_fingerprints": {
                    item.scenario_id: item.fingerprint
                    for item in assessment.results
                },
            },
        }

        if any(hasattr(item, "subject_content") for item in assessment.scenarios):
            artifacts["constitutional_certification_scenarios.json"] = {
                "schema_version": assessment.schema_version,
                "certification_fingerprint": assessment.certification_fingerprint,
                "scenarios": [item.to_dict() for item in assessment.scenarios],
                "results": [item.to_dict() for item in assessment.results],
            }

        written = []
        for name, payload in artifacts.items():
            path = output_directory / name
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            written.append(path)

        report = output_directory / "constitutional_certification_report.md"
        s = assessment.statistics
        report.write_text(
            "\n".join(
                [
                    "# Genesis VII-C4.1 Pack 2 Live Scenario Certification Report",
                    "",
                    f"**Certification fingerprint:** `{assessment.certification_fingerprint}`",
                    "",
                    "## Fingerprint chain",
                    "",
                    f"- Repository: `{assessment.repository_fingerprint}`",
                    f"- Extraction: `{assessment.extraction_fingerprint}`",
                    f"- Analysis: `{assessment.analysis_fingerprint}`",
                    f"- Ratification: `{assessment.ratification_fingerprint}`",
                    f"- Compliance: `{assessment.compliance_fingerprint}`",
                    "",
                    "## Live scenario statistics",
                    "",
                    f"- Scenarios executed: {s.scenarios}",
                    f"- Passed: {s.passed}",
                    f"- Failed: {s.failed}",
                    f"- Skipped: {s.skipped}",
                    f"- Positive findings: {s.positive_findings}",
                    f"- Negative findings: {s.negative_findings}",
                    f"- Review findings: {s.review_findings}",
                    f"- Not-applicable subjects: {s.not_applicable_subjects}",
                    f"- Diagnostics: {s.diagnostics}",
                    "",
                    "## Results",
                    "",
                    *[
                        (
                            f"- `{result.scenario_id}`: **{result.status.upper()}** — "
                            f"observed `{result.observed_status}`, "
                            f"article `{result.observed_article_id or 'none'}`, "
                            f"rank `{result.rank}`"
                        )
                        for result in assessment.results
                    ],
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(report)
        return tuple(written)

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.compliance import (  # noqa: E402
    COMPLIANCE_SCHEMA_VERSION,
    ConstitutionalComplianceEngine,
    ConstitutionalComplianceReporter,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 72)
    print("GENESIS VII-C4 — CONSTITUTIONAL COMPLIANCE ENGINE")
    print("=" * 72)

    ratification_dir = PROJECT_ROOT / "artifacts/audit/km0000-c3"
    subject_path = PROJECT_ROOT / "artifacts/audit/km0000-c4/compliance_subjects.json"
    output_dir = PROJECT_ROOT / "artifacts/audit/km0000-c4"

    if not subject_path.exists():
        subject_path.parent.mkdir(parents=True, exist_ok=True)
        subject_path.write_text(
            json.dumps(
                {
                    "subjects": [
                        {
                            "subject_id": "C4-SELF-001",
                            "subject_type": "architecture",
                            "path": "docs/architecture/governance/constitutional_compliance_engine.md",
                            "title": "Constitutional Compliance Engine",
                            "content": (
                                "The Constitutional Compliance Engine must preserve evidence, "
                                "retain traceability, remain deterministic, and require review "
                                "for unresolved constitutional conflicts."
                            ),
                            "domain": "governance",
                        }
                    ]
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    failures = 0
    engine = ConstitutionalComplianceEngine()
    first = engine.assess(ratification_dir, subject_path)
    second = engine.assess(ratification_dir, subject_path)

    failures += check(
        first.schema_version == COMPLIANCE_SCHEMA_VERSION,
        "Compliance schema is supported",
        first.schema_version,
    )
    failures += check(bool(first.repository_fingerprint), "Repository fingerprint linked", first.repository_fingerprint)
    failures += check(bool(first.extraction_fingerprint), "Extraction fingerprint linked", first.extraction_fingerprint)
    failures += check(bool(first.analysis_fingerprint), "Analysis fingerprint linked", first.analysis_fingerprint)
    failures += check(bool(first.ratification_fingerprint), "Ratification fingerprint linked", first.ratification_fingerprint)
    failures += check(
        first.compliance_fingerprint == second.compliance_fingerprint,
        "Compliance assessment is deterministic",
        first.compliance_fingerprint,
    )

    subject_ids = [item.subject_id for item in first.subjects]
    finding_ids = [item.finding_id for item in first.findings]
    assessment_ids = [item.subject_id for item in first.assessments]
    article_ids = {item.article_id for item in first.articles}

    failures += check(len(subject_ids) == len(set(subject_ids)), "Subject identifiers are unique", f"count={len(subject_ids)}")
    failures += check(len(finding_ids) == len(set(finding_ids)), "Finding identifiers are unique", f"count={len(finding_ids)}")
    failures += check(set(subject_ids) == set(assessment_ids), "Every subject has an assessment", f"subjects={len(subject_ids)}")
    failures += check(
        all(item.article_id in article_ids for item in first.findings),
        "Every finding references an existing article",
        f"findings={len(first.findings)}",
    )

    written = ConstitutionalComplianceReporter().write(first, output_dir)
    expected = {
        "constitutional_compliance.json",
        "constitutional_compliance_subjects.json",
        "constitutional_compliance_findings.json",
        "constitutional_compliance_assessments.json",
        "constitutional_compliance_traceability.json",
        "constitutional_compliance_report.md",
    }
    failures += check({path.name for path in written} == expected, "Canonical C4 artifact set", f"files={len(written)}")

    invalid = []
    for path in written:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid.append(path.name)
    failures += check(not invalid, "C4 JSON artifacts are valid", f"invalid={len(invalid)}")

    s = first.statistics
    print("-" * 72)
    print(f"Repository fingerprint   : {first.repository_fingerprint}")
    print(f"Extraction fingerprint   : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint     : {first.analysis_fingerprint}")
    print(f"Ratification fingerprint : {first.ratification_fingerprint}")
    print(f"Compliance fingerprint   : {first.compliance_fingerprint}")
    print(f"Subjects                 : {s.subjects}")
    print(f"Articles considered      : {s.articles_considered}")
    print(f"Findings                 : {s.findings}")
    print(f"Compliant findings       : {s.compliant_findings}")
    print(f"Review required          : {s.review_required_findings}")
    print(f"Noncompliant findings    : {s.noncompliant_findings}")
    print(f"Compliant subjects       : {s.compliant_subjects}")
    print(f"Review-required subjects : {s.review_required_subjects}")
    print(f"Noncompliant subjects    : {s.noncompliant_subjects}")
    print(f"Diagnostics              : {s.diagnostics}")
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from dev.reports import (
    AuditReport,
    EngineeringReportStatus,
    normalize_report,
)


def main() -> int:
    checks: list[dict[str, str]] = []

    def check(
        code: str,
        passed: bool,
        detail: str,
    ) -> None:
        checks.append(
            {
                "code": code,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    legacy = {
        "status": "FAILED",
        "classification": "NO_SEARCHABLE_KNOWLEDGE",
        "summary": {
            "known_raw_hits": 0,
            "known_qualified_hits": 0,
        },
        "recommendations": [
            "Populate chunk and FTS tables.",
        ],
    }

    report = normalize_report(
        legacy,
        title="Legacy Retrieval Audit",
    )

    check(
        "NORMALIZE-DICT",
        isinstance(report, AuditReport),
        type(report).__name__,
    )
    check(
        "STATUS-STABLE",
        report.status is EngineeringReportStatus.FAILED,
        report.status.value,
    )
    check(
        "JSON-STABLE",
        json.loads(report.to_json())[
            "classification"
        ]
        == "NO_SEARCHABLE_KNOWLEDGE",
        report.classification,
    )
    check(
        "MARKDOWN-STABLE",
        "Legacy Retrieval Audit"
        in report.to_markdown(),
        "title rendered",
    )

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        json_path = report.write_json(
            root / "report.json"
        )
        md_path = report.write_markdown(
            root / "report.md"
        )

        check(
            "WRITE-JSON",
            json_path.is_file(),
            str(json_path),
        )
        check(
            "WRITE-MARKDOWN",
            md_path.is_file(),
            str(md_path),
        )

    normalized_again = normalize_report(report)

    check(
        "IDEMPOTENT",
        normalized_again is report,
        "existing EngineeringReport returned unchanged",
    )

    failed = [
        item
        for item in checks
        if item["status"] != "PASS"
    ]
    status = "EXCELLENT" if not failed else "FAILED"

    root = Path.cwd().resolve()
    output = (
        root
        / "docs/audits/genesis_ix_a5_pack2"
    )
    output.mkdir(parents=True, exist_ok=True)

    certification = AuditReport(
        schema_version="genesis_ix_a5_pack2_cert_v1",
        status=(
            EngineeringReportStatus.EXCELLENT
            if not failed
            else EngineeringReportStatus.FAILED
        ),
        classification=(
            "ENGINEERING_REPORT_FRAMEWORK_CERTIFIED"
            if not failed
            else "ENGINEERING_REPORT_FRAMEWORK_FAILED"
        ),
        title=(
            "Genesis IX-A5 Pack 2 — "
            "Engineering Report Framework Certification"
        ),
        summary={
            "checks_executed": len(checks),
            "checks_passed": len(checks) - len(failed),
            "checks_failed": len(failed),
        },
        checks=tuple(checks),
        recommendations=(
            (
                "Use normalize_report() at legacy boundaries.",
                "Return EngineeringReport subclasses from new tools.",
            )
            if not failed
            else (
                "Repair failed framework checks before migration.",
            )
        ),
    )

    certification.write_json(
        output / "framework_certification.json"
    )
    certification.write_markdown(
        output / "framework_certification.md"
    )

    print("=" * 76)
    print("GENESIS IX-A5 PACK 2 — ENGINEERING REPORT FRAMEWORK")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", status)
    print("=" * 76)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

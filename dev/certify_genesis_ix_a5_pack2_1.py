from __future__ import annotations

import json
import tempfile
from pathlib import Path

from dev.reports import (
    AuditReport,
    EngineeringReportRenderer,
    EngineeringReportStatus,
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

    report = AuditReport(
        schema_version="renderer_cert_v1",
        status=EngineeringReportStatus.FAILED,
        classification="NO_SEARCHABLE_KNOWLEDGE",
        title="Knowledge Substrate Retrieval Audit",
        summary={
            "database_path": "/tmp/catalog.sqlite",
            "known_raw_hits": 0,
            "known_qualified_hits": 0,
            "fts_rows": 0,
            "chunk_rows": 0,
        },
        recommendations=(
            "Populate chunk tables.",
            "Rebuild FTS.",
        ),
    )

    markdown = EngineeringReportRenderer.render_markdown(
        report
    )
    terminal = EngineeringReportRenderer.render_terminal(
        report
    )
    payload = json.loads(
        EngineeringReportRenderer.render_json(report)
    )
    summary = EngineeringReportRenderer.render_summary(
        report
    )

    check(
        "MARKDOWN",
        "Knowledge Substrate Retrieval Audit"
        in markdown,
        "canonical markdown rendered",
    )
    check(
        "TERMINAL",
        "NO_SEARCHABLE_KNOWLEDGE"
        in terminal,
        "terminal classification rendered",
    )
    check(
        "JSON",
        payload["classification"]
        == "NO_SEARCHABLE_KNOWLEDGE",
        payload["classification"],
    )
    check(
        "SUMMARY",
        summary["status"] == "FAILED",
        summary["status"],
    )

    legacy = {
        "status": "FAILED",
        "classification": "LEGACY",
        "summary": {"database_path": "/tmp/legacy.sqlite"},
    }

    check(
        "LEGACY-MARKDOWN",
        "LEGACY"
        in EngineeringReportRenderer.render_markdown(
            legacy
        ),
        "legacy mapping normalized",
    )

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "report.md").write_text(
            markdown,
            encoding="utf-8",
        )
        (root / "report.json").write_text(
            EngineeringReportRenderer.render_json(
                report
            ),
            encoding="utf-8",
        )

        check(
            "FILES",
            (root / "report.md").is_file()
            and (root / "report.json").is_file(),
            "renderer outputs persisted",
        )

    failed = [
        item
        for item in checks
        if item["status"] != "PASS"
    ]

    status = (
        EngineeringReportStatus.EXCELLENT
        if not failed
        else EngineeringReportStatus.FAILED
    )

    certification = AuditReport(
        schema_version="genesis_ix_a5_pack2_1_cert_v1",
        status=status,
        classification=(
            "ENGINEERING_REPORT_RENDERER_CERTIFIED"
            if not failed
            else "ENGINEERING_REPORT_RENDERER_FAILED"
        ),
        title=(
            "Genesis IX-A5 Pack 2.1 — "
            "Engineering Report Renderer Certification"
        ),
        summary={
            "checks_executed": len(checks),
            "checks_passed": len(checks) - len(failed),
            "checks_failed": len(failed),
        },
        checks=tuple(checks),
        recommendations=(
            (
                "Use EngineeringReportRenderer for all new output surfaces.",
                "Normalize legacy inputs only at compatibility boundaries.",
            )
            if not failed
            else (
                "Repair failed renderer checks.",
            )
        ),
    )

    output = (
        Path.cwd()
        / "docs/audits/genesis_ix_a5_pack2_1"
    )
    output.mkdir(parents=True, exist_ok=True)

    (output / "renderer_certification.json").write_text(
        EngineeringReportRenderer.render_json(
            certification
        ),
        encoding="utf-8",
    )
    (output / "renderer_certification.md").write_text(
        EngineeringReportRenderer.render_markdown(
            certification
        ),
        encoding="utf-8",
    )

    print(
        EngineeringReportRenderer.render_terminal(
            certification
        ),
        end="",
    )

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

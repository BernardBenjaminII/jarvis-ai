"""Human-readable Engineering OS reporting."""

from __future__ import annotations

from pathlib import Path

from .compatibility import CompatibilityReport
from .restoration import RestorationRecommendation


def render_compatibility_markdown(
    report: CompatibilityReport,
    recommendations: tuple[RestorationRecommendation, ...],
) -> str:
    lines = [
        "# Public API Compatibility Report",
        "",
        f"**Compatibility score:** {report.compatibility_score:.2%}",
        f"**Report fingerprint:** `{report.fingerprint()}`",
        f"**Expected packages:** {len(report.expectations)}",
        f"**Findings:** {len(report.findings)}",
        "",
        "## Certification Result",
        "",
        "PASS" if not report.findings else "RESTORATION REQUIRED",
        "",
        "## Findings",
        "",
    ]

    if not report.findings:
        lines.append("No public API compatibility regressions were detected.")
    else:
        lines.extend([
            "| Package | Symbol | Type | Severity |",
            "|---|---|---|---|",
        ])
        for finding in report.findings:
            lines.append(
                f"| `{finding.package}` | `{finding.symbol}` | "
                f"{finding.finding_type} | {finding.severity} |"
            )

    lines.extend(["", "## Restoration Recommendations", ""])

    if not recommendations:
        lines.append("No restoration actions are required.")
    else:
        for recommendation in recommendations:
            lines.extend([
                f"### `{recommendation.package}.{recommendation.symbol}`",
                "",
                f"- **Action:** `{recommendation.action}`",
                f"- **Target:** `{recommendation.target_file}`",
                f"- **Source:** `{recommendation.source_module or 'not discovered'}`",
                f"- **Confidence:** {recommendation.confidence:.3f}",
                f"- **Rationale:** {recommendation.rationale}",
                "",
            ])

    lines.extend([
        "## Engineering Boundary",
        "",
        "This report is advisory. No source files were modified.",
        "",
    ])
    return "\n".join(lines)


def write_compatibility_report(
    report: CompatibilityReport,
    recommendations: tuple[RestorationRecommendation, ...],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_compatibility_markdown(report, recommendations),
        encoding="utf-8",
    )


__all__ = [
    "render_compatibility_markdown",
    "write_compatibility_report",
]

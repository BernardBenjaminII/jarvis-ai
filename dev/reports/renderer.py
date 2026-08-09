from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .contracts import EngineeringReport
from .normalize import normalize_report


@dataclass(frozen=True, slots=True)
class EngineeringReportRenderer:
    """Canonical renderer for all Genesis engineering reports."""

    @staticmethod
    def _report(value: Any) -> EngineeringReport:
        return normalize_report(value)

    @classmethod
    def render_json(
        cls,
        value: Any,
        *,
        indent: int = 2,
    ) -> str:
        report = cls._report(value)
        return (
            json.dumps(
                report.to_dict(),
                indent=indent,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def render_markdown(
        cls,
        value: Any,
    ) -> str:
        report = cls._report(value)
        return report.to_markdown()

    @classmethod
    def render_summary(
        cls,
        value: Any,
    ) -> dict[str, Any]:
        report = cls._report(value)

        return {
            "title": report.title,
            "status": report.status.value,
            "classification": report.classification,
            "kind": report.kind.value,
            "generated_at": report.generated_at,
            "summary": dict(report.summary),
            "warning_count": len(report.warnings),
            "recommendation_count": len(
                report.recommendations
            ),
            "check_count": len(report.checks),
            "passed": report.passed,
        }

    @classmethod
    def render_terminal(
        cls,
        value: Any,
        *,
        width: int = 76,
    ) -> str:
        report = cls._report(value)
        rule = "=" * max(40, width)

        lines = [
            rule,
            report.title.upper(),
            rule,
            f"Status         : {report.status.value}",
            f"Classification : {report.classification}",
            f"Kind           : {report.kind.value}",
            f"Generated      : {report.generated_at}",
        ]

        if report.summary:
            lines.extend(
                [
                    "-" * max(40, width),
                    "Summary",
                    "-" * max(40, width),
                ]
            )

            for key, item in sorted(
                report.summary.items(),
                key=lambda pair: str(pair[0]),
            ):
                lines.append(
                    f"{str(key):<24}: {item}"
                )

        if report.warnings:
            lines.extend(
                [
                    "-" * max(40, width),
                    "Warnings",
                    "-" * max(40, width),
                ]
            )
            lines.extend(
                f"- {item}"
                for item in report.warnings
            )

        if report.recommendations:
            lines.extend(
                [
                    "-" * max(40, width),
                    "Recommendations",
                    "-" * max(40, width),
                ]
            )
            lines.extend(
                f"- {item}"
                for item in report.recommendations
            )

        lines.append(rule)
        return "\n".join(lines) + "\n"

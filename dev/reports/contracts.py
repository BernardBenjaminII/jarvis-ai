from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


def _freeze_dicts(
    values: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]] | None,
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        MappingProxyType(dict(item))
        for item in (values or ())
    )


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _plain(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_plain(item) for item in value]

    if isinstance(value, list):
        return [_plain(item) for item in value]

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _plain(value.to_dict())

    return value


class EngineeringReportStatus(str, Enum):
    EXCELLENT = "EXCELLENT"
    PASSED = "PASSED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class EngineeringReportKind(str, Enum):
    ENGINEERING = "engineering"
    CERTIFICATION = "certification"
    AUDIT = "audit"
    VERIFICATION = "verification"
    MIGRATION = "migration"
    DIAGNOSTICS = "diagnostics"


@dataclass(frozen=True, slots=True)
class EngineeringReport:
    schema_version: str
    status: EngineeringReportStatus
    classification: str
    title: str
    summary: Mapping[str, Any] = field(default_factory=dict)
    checks: tuple[Mapping[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    generated_at: str = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    kind: EngineeringReportKind = EngineeringReportKind.ENGINEERING

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "summary",
            _freeze_mapping(self.summary),
        )
        object.__setattr__(
            self,
            "checks",
            _freeze_dicts(self.checks),
        )
        object.__setattr__(
            self,
            "warnings",
            tuple(str(item) for item in self.warnings),
        )
        object.__setattr__(
            self,
            "recommendations",
            tuple(
                str(item)
                for item in self.recommendations
            ),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

    @property
    def passed(self) -> bool:
        return self.status in {
            EngineeringReportStatus.EXCELLENT,
            EngineeringReportStatus.PASSED,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind.value,
            "status": self.status.value,
            "classification": self.classification,
            "title": self.title,
            "generated_at": self.generated_at,
            "summary": _plain(self.summary),
            "checks": _plain(self.checks),
            "warnings": list(self.warnings),
            "recommendations": list(
                self.recommendations
            ),
            "metadata": _plain(self.metadata),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return (
            json.dumps(
                self.to_dict(),
                indent=indent,
                sort_keys=True,
            )
            + "\n"
        )

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"**Status:** **{self.status.value}**",
            f"**Classification:** **{self.classification}**",
            f"**Generated:** {self.generated_at}",
            "",
            "## Summary",
            "",
        ]

        if self.summary:
            for key, value in sorted(
                self.summary.items(),
                key=lambda item: str(item[0]),
            ):
                lines.append(
                    f"- **{key}:** `{_plain(value)}`"
                )
        else:
            lines.append("- No summary values.")

        lines.extend(
            [
                "",
                "## Checks",
                "",
                "| Check | Status | Detail |",
                "|---|---|---|",
            ]
        )

        if self.checks:
            for check in self.checks:
                lines.append(
                    f"| `{check.get('code', 'CHECK')}` | "
                    f"**{check.get('status', 'UNKNOWN')}** | "
                    f"{check.get('detail', '')} |"
                )
        else:
            lines.append(
                "| `NONE` | **UNKNOWN** | No checks recorded. |"
            )

        lines.extend(["", "## Warnings", ""])

        if self.warnings:
            lines.extend(
                f"- {item}"
                for item in self.warnings
            )
        else:
            lines.append("- None.")

        lines.extend(
            ["", "## Recommendations", ""]
        )

        if self.recommendations:
            lines.extend(
                f"- {item}"
                for item in self.recommendations
            )
        else:
            lines.append("- None.")

        return "\n".join(lines) + "\n"

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.to_json(),
            encoding="utf-8",
        )
        return path

    def write_markdown(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.to_markdown(),
            encoding="utf-8",
        )
        return path


@dataclass(frozen=True, slots=True)
class CertificationReport(EngineeringReport):
    kind: EngineeringReportKind = (
        EngineeringReportKind.CERTIFICATION
    )


@dataclass(frozen=True, slots=True)
class AuditReport(EngineeringReport):
    kind: EngineeringReportKind = (
        EngineeringReportKind.AUDIT
    )


@dataclass(frozen=True, slots=True)
class VerificationReport(EngineeringReport):
    kind: EngineeringReportKind = (
        EngineeringReportKind.VERIFICATION
    )


@dataclass(frozen=True, slots=True)
class MigrationReport(EngineeringReport):
    kind: EngineeringReportKind = (
        EngineeringReportKind.MIGRATION
    )


@dataclass(frozen=True, slots=True)
class DiagnosticsReport(EngineeringReport):
    kind: EngineeringReportKind = (
        EngineeringReportKind.DIAGNOSTICS
    )

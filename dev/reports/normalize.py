from __future__ import annotations

from typing import Any, Mapping

from .contracts import (
    AuditReport,
    EngineeringReport,
    EngineeringReportKind,
    EngineeringReportStatus,
)


def _status(value: Any) -> EngineeringReportStatus:
    text = str(value or "UNKNOWN").upper()

    aliases = {
        "PASS": "PASSED",
        "OK": "PASSED",
        "SUCCESS": "PASSED",
    }
    text = aliases.get(text, text)

    try:
        return EngineeringReportStatus(text)
    except ValueError:
        return EngineeringReportStatus.UNKNOWN


def normalize_report(
    value: Any,
    *,
    title: str = "Engineering Report",
    classification: str = "LEGACY_NORMALIZED",
    schema_version: str = "engineering_report_v1",
    kind: EngineeringReportKind = (
        EngineeringReportKind.AUDIT
    ),
) -> EngineeringReport:
    if isinstance(value, EngineeringReport):
        return value

    if hasattr(value, "to_dict") and callable(value.to_dict):
        value = value.to_dict()

    if not isinstance(value, Mapping):
        raise TypeError(
            "Engineering report normalization requires an "
            "EngineeringReport, mapping, or object exposing to_dict(). "
            f"Received: {type(value).__name__}"
        )

    data = dict(value)

    checks = tuple(
        dict(item)
        for item in data.get("checks", ())
        if isinstance(item, Mapping)
    )

    known_keys = {
        "schema_version",
        "kind",
        "status",
        "classification",
        "title",
        "generated_at",
        "summary",
        "checks",
        "warnings",
        "recommendations",
        "metadata",
    }

    summary = data.get("summary")

    if not isinstance(summary, Mapping):
        summary = {
            key: item
            for key, item in data.items()
            if key not in known_keys
        }

    report_type = AuditReport

    return report_type(
        schema_version=str(
            data.get("schema_version")
            or schema_version
        ),
        status=_status(data.get("status")),
        classification=str(
            data.get("classification")
            or classification
        ),
        title=str(data.get("title") or title),
        generated_at=str(
            data.get("generated_at")
            or data.get("generated")
            or ""
        )
        or __import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        summary=dict(summary),
        checks=checks,
        warnings=tuple(
            str(item)
            for item in data.get("warnings", ())
        ),
        recommendations=tuple(
            str(item)
            for item in data.get(
                "recommendations",
                (),
            )
        ),
        metadata={
            **dict(
                data.get("metadata")
                if isinstance(
                    data.get("metadata"),
                    Mapping,
                )
                else {}
            ),
            "normalized_from": type(value).__name__,
            "requested_kind": kind.value,
        },
    )

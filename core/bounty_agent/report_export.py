"""R9.12: Read-only bounty investigation report exporter.

Produces review drafts, never automatic submissions.
Recon observations are not proof of a vulnerability.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


def _safe(value):
    """Keep untrusted observations within one Markdown line."""
    text = str(value if value is not None else "")
    return (
        text.replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "\\|")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "'")
        [:500]
    )


def _timestamp(value):
    if not isinstance(value, (int, float)):
        return "Not recorded"
    try:
        return datetime.fromtimestamp(
            value, timezone.utc
        ).isoformat()
    except (OverflowError, OSError, ValueError):
        return "Invalid timestamp"


def export_json(report):
    """Return a structured, portable copy of the report."""
    if not isinstance(report, dict):
        raise ValueError("Report must be a dictionary")
    if not isinstance(report.get("session"), dict):
        raise ValueError("Missing session")
    if not isinstance(report.get("mission"), dict):
        raise ValueError("Missing mission")

    return json.dumps(
        {
            "schema": "jarvis-bounty-report-r9.12",
            "report_type": "investigation_review_draft",
            "submission_status": "not_submitted",
            "vulnerability_confirmation": "not_asserted",
            "source": report,
        },
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )


def export_markdown(report):
    """Create a conservative, evidence-linked review report."""
    # Validate before rendering.
    export_json(report)

    session = report["session"]
    live = report["mission"]
    mission = live.get("mission") or {}
    tasks = live.get("tasks") or []
    plans = report.get("investigation_plans") or []
    options = report.get("options") or []

    lines = [
        "# JARVIS Bug Bounty Investigation",
        "",
        "**Status:** Draft — human review required",
        "",
        "**Submission:** Not submitted",
        "",
        "**Vulnerability confirmation:** Not asserted",
        "",
        "## Mission",
        "",
        f"- Program: {_safe(session.get('program'))}",
        f"- Target: {_safe(session.get('root_target'))}",
        f"- Session ID: {_safe(session.get('id'))}",
        f"- Authorization ID: {_safe(session.get('authorization'))}",
        f"- Session state: {_safe(session.get('state'))}",
        f"- Mission state: {_safe(mission.get('state'))}",
        f"- Task budget consumed: {_safe(mission.get('used'))}",
        "",
        "## Reconnaissance evidence",
        "",
        "| Task | Capability | Target | State | SHA-256 |",
        "|---|---|---|---|---|",
    ]

    for task in tasks:
        lines.append(
            "| " + " | ".join(
                _safe(task.get(key))
                for key in (
                    "id", "capability", "target",
                    "state", "evidence_sha256"
                )
            ) + " |"
        )

    if not tasks:
        lines.append(
            "| None | — | — | — | — |"
        )

    lines.extend([
        "",
        "## Investigation options",
        "",
    ])

    if not options:
        lines.append("No investigation options recorded.")
    else:
        for option in options:
            lines.append(
                f"- **{_safe(option.get('target'))}**: "
                f"priority {_safe(option.get('priority'))}; "
                f"review state {_safe(option.get('state'))}"
            )

    lines.extend([
        "",
        "## Investigation plans",
        "",
    ])

    if not plans:
        lines.append("No investigation plans recorded.")
    else:
        for wrapper in plans:
            plan = wrapper.get("plan", wrapper)
            if not isinstance(plan, dict):
                continue
            lines.append(
                f"- Plan {_safe(wrapper.get('id', plan.get('id')))}: "
                f"{_safe(plan.get('state', wrapper.get('state')))}"
            )

    lines.extend([
        "",
        "## Review requirements",
        "",
        "- Verify current program rules and approved scope.",
        "- Examine original evidence and SHA-256 references.",
        "- Confirm reproducibility and impact separately.",
        "- Obtain approval for any additional active validation.",
        "- Obtain human approval before submitting a report.",
        "",
        "Reconnaissance observations and investigation",
        " hypotheses are not independently confirmed vulnerabilities.",
        "",
        f"Exported at: {_timestamp(session.get('updated'))}",
        "",
    ])

    return "\n".join(lines)

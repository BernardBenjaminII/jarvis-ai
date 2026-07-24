from __future__ import annotations

import json
from typing import Any


def render_json(baseline: dict[str, Any]) -> str:
    return json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _flow(stages: list[str]) -> list[str]:
    lines = ["```text"]
    for index, stage in enumerate(stages):
        lines.append(stage)
        if index < len(stages) - 1:
            lines.append("        ↓")
    lines.append("```")
    return lines


def render_markdown(baseline: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Genesis I-A4 — Canonical Reasoning Architecture Baseline",
        "",
        f"**Baseline ID:** `{baseline['baseline_id']}`  ",
        f"**Version:** `{baseline['baseline_version']}`  ",
        f"**Status:** {baseline['status']}  ",
        f"**Fingerprint:** `{baseline['baseline_fingerprint']}`  ",
        "**Production code modified:** No",
        "",
        "## Executive Summary",
        "",
        baseline["executive_summary"],
        "",
        "## Source Audits",
        "",
        "| Phase | Audit | Source | Fingerprint |",
        "|---|---|---|---|",
    ]
    for report in baseline["source_reports"]:
        lines.append(f"| {report['phase']} | `{report['audit_id']}` | `{report['path']}` | `{report['fingerprint']}` |")

    lines += ["", "## Current Canonical Processing Flow", ""] + _flow(baseline["current_processing_flow"])
    lines += ["", "## Canonical Components", ""]
    for component in baseline["canonical_components"]:
        lines += [
            f"### `{component['name']}`",
            "",
            f"**Layer:** {component['layer']}  ",
            f"**Stability:** {component['stability']}",
            "",
            component["responsibility"],
            "",
            "**Owns**",
            "",
        ]
        lines += [f"- {item}" for item in component["owns"]]
        lines += ["", "**Must not own**", ""]
        lines += [f"- {item}" for item in component["must_not_own"]]
        lines += ["", "**Source modules**", ""]
        lines += [f"- `{item}`" for item in component["source_modules"]]
        lines += ["", f"**Extension policy:** {component['extension_policy']}", ""]

    lines += ["## Reasoning Engine Constitution", "", "These invariants are binding architecture rules.", ""]
    for invariant in baseline["constitutional_invariants"]:
        protected = ", ".join(f"`{name}`" for name in invariant["protected_components"])
        lines += [
            f"### {invariant['invariant_id']} — {invariant['title']}",
            "",
            f"**Rule:** {invariant['rule']}",
            "",
            f"**Rationale:** {invariant['rationale']}",
            "",
            f"**Protected components:** {protected}",
            "",
            f"**Validation:** {invariant['validation']}",
            "",
        ]

    lines += ["## Approved Extension Points", ""]
    for extension in baseline["approved_extension_points"]:
        lines += [
            f"### `{extension['name']}`",
            "",
            f"**Intended phase:** {extension['intended_phase']}",
            "",
            extension["purpose"],
            "",
            "**Allowed responsibilities**",
            "",
        ]
        lines += [f"- {item}" for item in extension["allowed_responsibilities"]]
        lines += ["", "**Prohibited responsibilities**", ""]
        lines += [f"- {item}" for item in extension["prohibited_responsibilities"]]
        lines += ["", f"**Compatibility requirement:** {extension['compatibility_requirement']}", ""]

    lines += ["## Target Generation 2 Flow", ""] + _flow(baseline["target_generation_2_flow"])
    lines += [
        "",
        "## Final Architectural Declaration",
        "",
        "The JARVIS Reasoning Engine converts explicit evidence and hypotheses into an auditable conclusion and advisory planning recommendation. It does not invisibly retrieve knowledge, authorize actions, execute missions, or rewrite historical reasoning.",
        "",
        "## Next Step",
        "",
        f"**{baseline['next_step']['phase']} — {baseline['next_step']['deliverable']}**",
        "",
        f"Then proceed to **{baseline['next_step']['then']}**.",
        "",
    ]
    return "\n".join(lines)

#!/usr/bin/env python3
"""Verify the Phase IX-C1 cognitive convergence inventory."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "generated_at_utc",
    "project_root",
    "git_branch",
    "executive_python_files",
    "planning_locations",
    "planning_location_symbols",
    "duplicate_symbols",
    "cognitive_documents",
    "root_whitepapers",
    "findings",
    "recommendations",
}

EXPECTED_PLANNING_LOCATIONS = {
    "core/executive/planner.py",
    "core/executive/planning",
    "core/executive/planning_engine",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(
            "Inventory JSON root must be an object"
        )

    return payload


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    report_path = (
        project_root
        / "docs"
        / "architecture"
        / "convergence"
        / "phase_9c1_inventory.json"
    )
    markdown_path = (
        project_root
        / "docs"
        / "architecture"
        / "convergence"
        / "phase_9c1_inventory.md"
    )

    failures: list[str] = []

    if not report_path.is_file():
        failures.append(
            f"Missing JSON inventory: {report_path}"
        )

    if not markdown_path.is_file():
        failures.append(
            f"Missing Markdown inventory: {markdown_path}"
        )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")

        return 1

    try:
        payload = load_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] Could not read inventory: {exc}")
        return 1

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(payload)

    if missing_keys:
        failures.append(
            "Missing report keys: "
            + ", ".join(sorted(missing_keys))
        )

    executive_files = payload.get(
        "executive_python_files",
        [],
    )

    if not isinstance(executive_files, list):
        failures.append(
            "executive_python_files must be a list"
        )
    elif not executive_files:
        failures.append(
            "No Executive Python files were inventoried"
        )
    else:
        invalid_files = [
            record.get("path", "<unknown>")
            for record in executive_files
            if not record.get("syntax_valid", False)
        ]

        if invalid_files:
            failures.append(
                "Syntax-invalid Executive files: "
                + ", ".join(invalid_files)
            )

    planning_locations = payload.get(
        "planning_locations",
        {},
    )

    if not isinstance(planning_locations, dict):
        failures.append(
            "planning_locations must be an object"
        )
    else:
        missing_locations = (
            EXPECTED_PLANNING_LOCATIONS
            - set(planning_locations)
        )

        if missing_locations:
            failures.append(
                "Missing planning inventory locations: "
                + ", ".join(sorted(missing_locations))
            )

    recommendations = payload.get(
        "recommendations",
        [],
    )

    if not isinstance(recommendations, list) or not recommendations:
        failures.append(
            "The audit produced no recommendations"
        )

    markdown_text = markdown_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    required_markdown_sections = (
        "# Phase IX-C1 Cognitive Architecture Inventory",
        "## Planning implementation locations",
        "## Duplicate public symbols",
        "## Root-level whitepaper disposition",
        "## Recommendations",
    )

    for section in required_markdown_sections:
        if section not in markdown_text:
            failures.append(
                f"Missing Markdown section: {section}"
            )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")

        return 1

    print(
        "[PASS] Cognitive convergence inventory "
        "is complete and structurally valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

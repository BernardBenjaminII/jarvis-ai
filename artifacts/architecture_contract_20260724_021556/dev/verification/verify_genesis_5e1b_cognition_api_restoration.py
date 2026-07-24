#!/usr/bin/env python3
"""Verify Genesis V-E1B cognition API restoration."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# Direct execution places dev/verification on sys.path, not the repository root.
# Add the repository root before importing project packages.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXPECTED = (
    "Assumption",
    "CognitiveWorkspaceCatalog",
    "CognitiveWorkspaceCodec",
    "CognitiveWorkspaceConflictError",
    "CognitiveWorkspaceNotFoundError",
    "CognitiveWorkspaceService",
    "EvidenceReference",
    "Hypothesis",
    "OpenQuestion",
    "SQLiteCognitiveWorkspaceRepository",
    "SortDirection",
    "WorkspaceQuery",
    "WorkspaceSortField",
    "WorkspaceStatus",
)


def check(condition: bool, label: str) -> int:
    """Print a deterministic verification result."""

    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def run(
    command: list[str],
    *,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a verification command from the repository root."""

    environment = os.environ.copy()
    environment["PYTHONPATH"] = (
        f"{ROOT}{os.pathsep}{environment['PYTHONPATH']}"
        if environment.get("PYTHONPATH")
        else str(ROOT)
    )
    environment["PYTHON_BIN"] = sys.executable

    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def main() -> int:
    """Execute the Genesis V-E1B verification suite."""

    failures = 0

    cognition = importlib.import_module("core.cognition")

    failures += check(
        all(hasattr(cognition, name) for name in EXPECTED),
        "Fourteen cognition compatibility exports",
    )

    exported_names = tuple(getattr(cognition, "__all__", ()))

    failures += check(
        all(name in exported_names for name in EXPECTED),
        "Cognition __all__ compatibility surface",
    )

    compile_result = run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/cognition",
            "dev/execute_genesis_5e1b_cognition_api_restoration.py",
            "dev/verification/verify_genesis_5e1b_cognition_api_restoration.py",
        ]
    )

    failures += check(
        compile_result.returncode == 0,
        "Restored cognition compilation",
    )

    analysis = run(
        [
            "bash",
            "dev/analyze_public_api_compatibility.sh",
        ]
    )

    failures += check(
        analysis.returncode == 0,
        "Compatibility analyzer execution",
    )

    evidence_path = (
        ROOT
        / ".artifacts"
        / "engineering"
        / "public_api_compatibility.json"
    )

    failures += check(
        evidence_path.is_file(),
        "Compatibility JSON evidence",
    )

    findings: list[dict[str, object]] = []

    if evidence_path.is_file():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        findings = list(evidence.get("findings", []))

    cognition_export_findings = [
        item
        for item in findings
        if item.get("package") == "core.cognition"
    ]

    failures += check(
        not cognition_export_findings,
        "All core.cognition missing exports resolved",
    )

    unresolved_cognitive_object = [
        item
        for item in findings
        if item.get("package")
        == "core.cognition.common.cognitive_object"
        and item.get("symbol") == "CognitiveObject"
    ]

    failures += check(
        len(unresolved_cognitive_object) <= 1,
        "CognitiveObject remains a single governed investigation",
    )

    archaeology_path = (
        ROOT
        / "docs"
        / "audits"
        / "cognitive_object_archaeology.md"
    )

    archaeology_valid = (
        archaeology_path.is_file()
        and "NO AUTOMATIC CHANGE"
        in archaeology_path.read_text(encoding="utf-8")
    )

    failures += check(
        archaeology_valid,
        "CognitiveObject archaeology evidence",
    )

    ve1a_result = run(
        [
            sys.executable,
            "dev/verification/"
            "verify_genesis_5e1a_repository_reality_modeling.py",
        ]
    )

    failures += check(
        ve1a_result.returncode == 0,
        "Genesis V-E1A regression",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        f"{'EXCELLENT' if failures == 0 else 'FAILED'}"
    )
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify Genesis V-E1C Static Public Surface Engine."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
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
        text=True,
    )


def forbidden_authority(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "httpx",
        "importlib",
    }
    findings: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in forbidden:
                    findings.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in forbidden:
                findings.add(module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                findings.add(node.func.id)

    return tuple(sorted(findings))


def main() -> int:
    failures = 0

    required = (
        ROOT / "core/engineering/public_surface.py",
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "tests/test_genesis_5e1c_static_public_surface.py",
        ROOT / "docs/engineering/genesis_v_e1c_static_public_surface.md",
    )
    failures += check(
        all(path.is_file() for path in required),
        "V-E1C required files",
    )

    compile_result = run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/engineering/public_surface.py",
            "core/engineering/api_inventory.py",
            "tests/test_genesis_5e1c_static_public_surface.py",
            "dev/verification/verify_genesis_5e1c_static_public_surface.py",
        ]
    )
    failures += check(
        compile_result.returncode == 0,
        "V-E1C compilation",
    )

    authority_findings = forbidden_authority(
        ROOT / "core/engineering/public_surface.py"
    )
    failures += check(
        not authority_findings,
        "Static evaluator has no runtime import, process, or network authority",
    )

    tests_result = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1c_static_public_surface",
        ]
    )
    failures += check(
        tests_result.returncode == 0,
        "V-E1C unit tests",
    )

    analyzer_result = run(
        [
            "bash",
            "dev/analyze_public_api_compatibility.sh",
        ]
    )
    failures += check(
        analyzer_result.returncode == 0,
        "Compatibility analyzer execution",
    )

    evidence_path = (
        ROOT
        / ".artifacts"
        / "engineering"
        / "public_api_compatibility.json"
    )
    evidence_exists = evidence_path.is_file()
    failures += check(
        evidence_exists,
        "Compatibility JSON evidence",
    )

    findings: list[dict[str, object]] = []
    score = 0.0
    if evidence_exists:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        findings = list(payload.get("findings", ()))
        score = float(payload.get("compatibility_score", 0.0))

    cognition_findings = [
        finding
        for finding in findings
        if str(finding.get("package", "")).startswith("core.cognition")
    ]
    failures += check(
        not cognition_findings,
        "Cognition compatibility findings eliminated",
    )

    failures += check(
        score == 1.0,
        "Public API compatibility score is 100%",
    )

    ve1_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1_public_api_compatibility.py",
        ]
    )
    failures += check(
        ve1_result.returncode == 0,
        "Genesis V-E1 regression",
    )

    ve1a_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1a_repository_reality_modeling.py",
        ]
    )
    failures += check(
        ve1a_result.returncode == 0,
        "Genesis V-E1A regression",
    )

    ve1b_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1b_cognition_api_restoration.py",
        ]
    )
    failures += check(
        ve1b_result.returncode == 0,
        "Genesis V-E1B regression",
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

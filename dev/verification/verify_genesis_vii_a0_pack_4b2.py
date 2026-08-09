
#!/usr/bin/env python3
"""Structural and behavioral certification for Genesis VII-A0 Pack 4B-2."""

from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "core/executive/capabilities/__init__.py",
    "core/executive/capabilities/models.py",
    "core/executive/capabilities/registry.py",
    "core/executive/capabilities/graph.py",
    "core/executive/capabilities/selector.py",
    "core/executive/capabilities/planner.py",
    "core/executive/capabilities/orchestrator.py",
    "core/executive/capabilities/observability.py",
    "tests/test_genesis_vii_a0_pack_4b2.py",
    "docs/architecture/genesis_vii_a0_pack_4b2_capability_orchestration.md",
)


def check(label: str, condition: bool) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0
    print("=" * 72)
    print("JARVIS — GENESIS VII-A0 PACK 4B-2")
    print("EXECUTIVE CAPABILITY ORCHESTRATION LAYER")
    print("=" * 72)

    failures += check("Canonical Pack 4B-2 file set", all((ROOT / item).is_file() for item in FILES))

    compile_result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(ROOT / "core/executive/capabilities")],
        cwd=ROOT,
    )
    failures += check("Python compilation", compile_result.returncode == 0)

    prohibited = ("openai", "anthropic", "ollama", "requests", "httpx", "subprocess")
    violations = []
    for relative in FILES[:8]:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(name.startswith(prohibited) for name in names):
                violations.append(relative)
    failures += check("Vendor, network, and execution isolation", not violations)

    test_result = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "tests.test_genesis_vii_a0_pack_4b2"],
        cwd=ROOT,
    )
    failures += check("Pack 4B-2 unit tests", test_result.returncode == 0)

    digest = sha256()
    for relative in FILES:
        digest.update(relative.encode())
        digest.update((ROOT / relative).read_bytes())
    print(f"[PASS] Deterministic pack fingerprint — {digest.hexdigest()}")

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

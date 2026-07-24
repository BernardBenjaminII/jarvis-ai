#!/usr/bin/env python3
"""Verification for Phase X-C2."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = os.environ.get("PYTHON_BIN") or sys.executable

FILES = (
    Path("core/representation/contracts.py"),
    Path("core/representation/segmentation.py"),
    Path("core/representation/articulation.py"),
    Path("core/representation/context.py"),
    Path("tests/test_phase_xc2_semantic_articulation.py"),
    Path("docs/architecture/cognitive_semantic_articulation.md"),
    Path("dev/verify_phase_xc2.sh"),
)

SYMBOLS = {
    Path("core/representation/articulation.py"): {
        "ArticulationKind", "SegmentReference", "ArticulatedUnit",
        "ArticulationResult", "ArticulationPolicy", "SemanticArticulator",
    },
    Path("core/representation/context.py"): {
        "ContextPolicy", "ContextEntry", "ContextWindow", "ContextAssembler",
    },
}


class Failure(RuntimeError):
    pass


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHON_BIN": PYTHON_BIN},
        capture_output=True,
        text=True,
        check=False,
    )


def required_files() -> None:
    missing = [str(path) for path in FILES if not (ROOT / path).is_file()]
    if missing:
        raise Failure("Missing files: " + ", ".join(missing))


def syntax() -> None:
    for path in FILES:
        if path.suffix == ".py":
            ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))


def symbols() -> None:
    for path, expected in SYMBOLS.items():
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))
        found = {
            node.name for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        }
        missing = expected - found
        if missing:
            raise Failure(f"{path} missing: {', '.join(sorted(missing))}")


def imports() -> None:
    completed = run(
        PYTHON_BIN,
        "-c",
        "from core.representation.articulation import SemanticArticulator; "
        "from core.representation.context import ContextAssembler",
    )
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def unit_tests() -> None:
    completed = run(
        PYTHON_BIN,
        "-m",
        "unittest",
        "-v",
        "tests.test_phase_xc2_semantic_articulation",
    )
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def deterministic_smoke() -> None:
    script = """
from dataclasses import dataclass
from core.representation.articulation import SemanticArticulator
from core.representation.context import ContextAssembler
@dataclass(frozen=True)
class S:
    segment_id: str
    ordinal: int
    kind: str
    text: str
    provenance: dict
s = (
    S("h", 0, "heading", "Readiness", {"source_id": "smoke"}),
    S("a", 1, "sentence", "One statement.", {"source_id": "smoke"}),
    S("b", 2, "sentence", "Second statement.", {"source_id": "smoke"}),
)
a = SemanticArticulator().articulate(s)
b = SemanticArticulator().articulate(tuple(reversed(s)))
assert a.fingerprint == b.fingerprint
ca = ContextAssembler().assemble(a.units, source_id=a.source_id)
cb = ContextAssembler().assemble(b.units, source_id=b.source_id)
assert ca.fingerprint == cb.fingerprint
"""
    completed = run(PYTHON_BIN, "-c", script)
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def boundaries() -> None:
    forbidden = (
        "core.executive", "core.mission", "core.planning",
        "knowledge_engine", "openai", "ollama", "requests", "httpx",
    )
    for path in (
        Path("core/representation/articulation.py"),
        Path("core/representation/context.py"),
    ):
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        bad = [
            name for name in imported
            if any(name == root or name.startswith(root + ".") for root in forbidden)
        ]
        if bad:
            raise Failure(f"{path} boundary violations: {', '.join(bad)}")


def main() -> int:
    checks = (
        ("Phase X-C1 prerequisites and X-C2 files", required_files),
        ("Python syntax", syntax),
        ("Required symbols", symbols),
        ("Stable module imports", imports),
        ("Unit tests", unit_tests),
        ("Deterministic smoke test", deterministic_smoke),
        ("Forward-only boundaries", boundaries),
    )
    failures: list[str] = []

    print()
    print("=" * 70)
    print("JARVIS PHASE X-C2 — SEMANTIC ARTICULATION VERIFICATION")
    print("=" * 70)

    for label, check in checks:
        try:
            check()
            print(f"[PASS] {label}")
        except Exception as exc:
            failures.append(f"{label}: {exc}")
            print(f"[FAIL] {label}: {exc}")

    print("-" * 70)
    print(f"Checks executed : {len(checks)}")
    print(f"Checks failed   : {len(failures)}")
    print("Overall status  : " + ("EXCELLENT" if not failures else "FAILED"))
    print("=" * 70)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

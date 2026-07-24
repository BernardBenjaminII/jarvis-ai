from __future__ import annotations

import os
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    "core/knowledge_awareness/__init__.py",
    "core/knowledge_awareness/contracts.py",
    "core/knowledge_awareness/service.py",
    "core/conversation/orchestrator.py",
    "tests/__init__.py",
    "tests/test_convergence_c5_executive_knowledge_awareness.py",
    "docs/architecture/convergence_c5_executive_knowledge_awareness.md",
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    prior = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{ROOT}{os.pathsep}{prior}" if prior else str(ROOT)
    )
    return environment


def _run_test_module(module_name: str) -> int:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            module_name,
        ],
        cwd=ROOT,
        env=_environment(),
        check=False,
    )
    return completed.returncode


def main() -> int:
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-5 EXECUTIVE KNOWLEDGE AWARENESS")
    print("=" * 72)

    failed = 0

    missing = [relative for relative in REQUIRED if not (ROOT / relative).exists()]
    for relative in missing:
        print(f"[FAIL] Missing {relative}")
        failed += 1
    if not missing:
        print("[PASS] Canonical C-5 file set")

    compile_failures = 0
    for relative in REQUIRED:
        if not relative.endswith(".py") or not (ROOT / relative).exists():
            continue
        try:
            py_compile.compile(str(ROOT / relative), doraise=True)
        except Exception as exc:  # pragma: no cover - verifier diagnostic path
            print(f"[FAIL] Compile {relative}: {exc}")
            compile_failures += 1
            failed += 1
    if compile_failures == 0:
        print("[PASS] Python compilation contract")

    orchestrator_path = ROOT / "core/conversation/orchestrator.py"
    if orchestrator_path.exists():
        text = orchestrator_path.read_text(encoding="utf-8")
        missing_tokens = [
            token
            for token in (
                "knowledge.awareness",
                "executive_knowledge_state",
                "executive_evidence_reasoning",
            )
            if token not in text
        ]
        for token in missing_tokens:
            print(f"[FAIL] Missing integration token {token}")
            failed += 1
        if not missing_tokens:
            print("[PASS] Executive orchestration integration")

    print("-" * 72)
    print(f"Checks failed : {failed}")
    print("Overall status:", "EXCELLENT" if failed == 0 else "FAILED")

    if failed:
        return 1

    print()
    print("[RUN] C-5 deterministic unit tests")
    result = _run_test_module(
        "tests.test_convergence_c5_executive_knowledge_awareness"
    )
    if result != 0:
        print("[FAIL] C-5 deterministic unit tests")
        return result

    print("[PASS] C-5 deterministic unit tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

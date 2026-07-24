#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "core/conversation/grounding.py",
    "core/conversation/orchestrator.py",
    "core/conversation/__init__.py",
    "core/src/routes/api.py",
    "tests/test_convergence_c4_knowledge_grounding.py",
    "docs/architecture/convergence_c4_knowledge_grounding.md",
    "dev/verify_convergence_c4.sh",
]


def main() -> int:
    failures = 0
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-4 KNOWLEDGE GROUNDING")
    print("=" * 72)

    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        failures += 1
        print("[FAIL] Canonical C-4 file set:", ", ".join(missing))
    else:
        print("[PASS] Canonical C-4 file set")

    try:
        for item in REQUIRED:
            if item.endswith(".py"):
                py_compile.compile(str(ROOT / item), doraise=True)
        print("[PASS] Python compilation contract")
    except Exception as exc:
        failures += 1
        print(f"[FAIL] Python compilation contract: {exc}")

    grounding = (ROOT / "core/conversation/grounding.py").read_text()
    orchestrator = (ROOT / "core/conversation/orchestrator.py").read_text()
    api = (ROOT / "core/src/routes/api.py").read_text()

    checks = [
        ("Catalog grounding declares evidence and gaps", "class KnowledgeGap" in grounding and "class GroundingEvidence" in grounding),
        ("Executive synthesis receives grounded context", "synthesis_input" in orchestrator and "knowledge.grounding" in orchestrator),
        ("Production API activates the live Knowledge Director", "knowledge_search=catalog_grounding.search_for_director" in api),
        ("Catalog database path remains configurable", "JARVIS_CATALOG_DB" in api),
    ]
    for label, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        failures += 0 if ok else 1

    digest = hashlib.sha256()
    for item in sorted(REQUIRED):
        digest.update(item.encode())
        digest.update((ROOT / item).read_bytes())
    print("Architecture fingerprint:", digest.hexdigest())
    print("-" * 72)
    print("Checks failed :", failures)
    print("Overall status:", "EXCELLENT" if failures == 0 else "FAILED")
    print("=" * 72)
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())

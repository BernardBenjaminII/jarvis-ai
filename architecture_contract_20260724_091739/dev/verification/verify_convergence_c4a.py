#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "core/knowledge_catalog/database.py",
    "tests/test_convergence_c1_http_contract.py",
    "tests/test_convergence_c2_http_contract.py",
    "tests/test_convergence_c4a_knowledge_compatibility.py",
    "docs/architecture/convergence_c4a_knowledge_compatibility_repair.md",
    "dev/verification/verify_convergence_c4a.py",
    "dev/verify_convergence_c4a.sh",
]


def main() -> int:
    failures = 0
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-4A KNOWLEDGE COMPATIBILITY REPAIR")
    print("=" * 72)

    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        failures += 1
        print("[FAIL] Canonical C-4A file set:", ", ".join(missing))
    else:
        print("[PASS] Canonical C-4A file set")

    try:
        for item in REQUIRED:
            if item.endswith(".py"):
                py_compile.compile(str(ROOT / item), doraise=True)
        print("[PASS] Python compilation contract")
    except Exception as exc:
        failures += 1
        print(f"[FAIL] Python compilation contract: {exc}")

    database_text = (ROOT / "core/knowledge_catalog/database.py").read_text()
    c1_text = (ROOT / "tests/test_convergence_c1_http_contract.py").read_text()
    c2_text = (ROOT / "tests/test_convergence_c2_http_contract.py").read_text()

    checks = [
        (
            "Optional STRUCTURE_SQL no longer blocks catalog import",
            'getattr(catalog_schema, name, "")' in database_text
            and 'structure_sql = _schema_script("STRUCTURE_SQL")' in database_text,
        ),
        (
            "Required schema scripts remain enforced",
            "Required Knowledge Catalog schema missing" in database_text,
        ),
        (
            "C-1 HTTP contract accepts grounding enrichment",
            'startswith("ok:status")' in c1_text and '"knowledge_grounding"' in c1_text,
        ),
        (
            "C-2 HTTP contract accepts grounding enrichment",
            'startswith("SYNTHESIZED: Search the catalog")' in c2_text
            and '"knowledge_grounding"' in c2_text,
        ),
        (
            "Production grounding remains present",
            (ROOT / "core/conversation/grounding.py").is_file(),
        ),
    ]
    for label, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")
        failures += 0 if passed else 1

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

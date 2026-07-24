"""Certification verifier for JARVIS Convergence C-2A."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "tests/test_convergence_c1_http_contract.py",
    "tests/test_convergence_c2_http_contract.py",
    "tests/test_convergence_c2a_certification_repair.py",
    "dev/verification/verify_convergence_c2a.py",
    "dev/verify_convergence_c2a.sh",
    "docs/architecture/convergence_c2a_certification_repair.md",
)


def check(label: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-2A CERTIFICATION REPAIR")
    print("=" * 72)
    results: list[bool] = []

    results.append(check("Canonical C-2A file set", all((ROOT / path).is_file() for path in REQUIRED)))

    parse_ok = True
    for path in REQUIRED:
        if not path.endswith(".py"):
            continue
        try:
            ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        except Exception as exc:
            parse_ok = False
            print(f"       {path}: {exc}")
    results.append(check("Python compilation contract", parse_ok))

    c1_http = (ROOT / "tests/test_convergence_c1_http_contract.py").read_text(encoding="utf-8")
    c2_http = (ROOT / "tests/test_convergence_c2_http_contract.py").read_text(encoding="utf-8")
    route = (ROOT / "core/src/routes/api.py").read_text(encoding="utf-8")

    results.append(check(
        "Outdated C-1 answer-handler patch removed",
        "conversation_service, \"answer_handler\"" not in c1_http,
    ))
    results.append(check(
        "HTTP contracts inject deterministic synthesis",
        "synthesis_handler" in c1_http and "synthesis_handler" in c2_http,
    ))
    results.append(check(
        "Production orchestration remains untouched",
        "synthesis_handler=route_question" in route and "conversation_orchestrator" in route,
    ))

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for module in (
        "tests.test_convergence_c1_executive_conversation",
        "tests.test_convergence_c1_http_contract",
        "tests.test_convergence_c2_director_activation",
        "tests.test_convergence_c2_http_contract",
        "tests.test_convergence_c2a_certification_repair",
    ):
        suite.addTests(loader.loadTestsFromName(module))
    test_result = unittest.TextTestRunner(verbosity=1).run(suite)
    results.append(check("C-1, C-2, and C-2A deterministic tests", test_result.wasSuccessful()))

    digest = hashlib.sha256()
    for path in REQUIRED:
        digest.update(path.encode("utf-8"))
        digest.update((ROOT / path).read_bytes())
    print(f"Architecture fingerprint: {digest.hexdigest()}")

    failures = results.count(False)
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

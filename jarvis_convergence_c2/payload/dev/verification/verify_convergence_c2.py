from pathlib import Path
import ast
import hashlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/conversation/orchestrator.py",
    "core/conversation/service.py",
    "core/conversation/__init__.py",
    "core/src/routes/api.py",
    "tests/test_convergence_c2_director_activation.py",
    "tests/test_convergence_c2_http_contract.py",
    "docs/architecture/convergence_c2_director_activation.md",
)


def check(label, condition):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-2 DIRECTOR ACTIVATION")
    print("=" * 72)
    results = []
    results.append(check("Canonical C-2 file set", all((ROOT / path).is_file() for path in REQUIRED)))
    parse_ok = True
    for path in REQUIRED:
        if path.endswith(".py"):
            try:
                ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
            except Exception as exc:
                parse_ok = False
                print(f"       {path}: {exc}")
    results.append(check("Python compilation contract", parse_ok))
    service = (ROOT / "core/conversation/service.py").read_text(encoding="utf-8")
    route = (ROOT / "core/src/routes/api.py").read_text(encoding="utf-8")
    orchestrator = (ROOT / "core/conversation/orchestrator.py").read_text(encoding="utf-8")
    results.append(check("C-1 boundary upgraded in place", "ExecutiveConversationOrchestrator" in service))
    results.append(check("Existing ExecutiveDirector activated", "ExecutiveDirector" in orchestrator and ".submit(" in orchestrator))
    results.append(check("HTTP route uses director orchestration", "conversation_orchestrator" in route))
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for module in (
        "tests.test_convergence_c1_executive_conversation",
        "tests.test_convergence_c1_http_contract",
        "tests.test_convergence_c2_director_activation",
        "tests.test_convergence_c2_http_contract",
    ):
        suite.addTests(loader.loadTestsFromName(module))
    test_result = unittest.TextTestRunner(verbosity=1).run(suite)
    results.append(check("C-1 and C-2 tests", test_result.wasSuccessful()))
    digest = hashlib.sha256()
    for path in REQUIRED:
        digest.update(path.encode())
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

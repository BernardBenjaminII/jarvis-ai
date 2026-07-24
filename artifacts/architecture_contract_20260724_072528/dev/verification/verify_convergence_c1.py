from pathlib import Path
import ast
import hashlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/conversation/__init__.py",
    "core/conversation/contracts.py",
    "core/conversation/compiler.py",
    "core/conversation/repository.py",
    "core/conversation/service.py",
    "core/src/routes/api.py",
    "core/src/static/mission_control/index.html",
    "core/src/static/mission_control/app.js",
    "core/src/static/mission_control/styles.css",
    "tests/test_convergence_c1_executive_conversation.py",
    "tests/test_convergence_c1_http_contract.py",
    "docs/architecture/convergence_c1_executive_conversation.md",
)


def check(label, condition):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 72)
    print("JARVIS — CONVERGENCE C-1 EXECUTIVE CONVERSATION")
    print("=" * 72)
    results = []
    results.append(check("Canonical C-1 file set", all((ROOT / path).is_file() for path in REQUIRED)))
    parse_ok = True
    for path in REQUIRED:
        if path.endswith(".py"):
            try: ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
            except Exception as exc:
                parse_ok = False
                print(f"       {path}: {exc}")
    results.append(check("Python compilation contract", parse_ok))
    api_text = (ROOT / "core/src/routes/api.py").read_text(encoding="utf-8")
    results.append(check("Canonical conversation endpoint", '/api/conversation/query' in api_text))
    ui_text = (ROOT / "core/src/static/mission_control/index.html").read_text(encoding="utf-8")
    js_text = (ROOT / "core/src/static/mission_control/app.js").read_text(encoding="utf-8")
    results.append(check("Bridge conversation surface", 'conversation-form' in ui_text and '/api/conversation/query' in js_text))
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for module in (
        "tests.test_convergence_c1_executive_conversation",
        "tests.test_convergence_c1_http_contract",
    ):
        suite.addTests(loader.loadTestsFromName(module))
    test_result = unittest.TextTestRunner(verbosity=1).run(suite)
    results.append(check("C-1 unit and HTTP tests", test_result.wasSuccessful()))
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

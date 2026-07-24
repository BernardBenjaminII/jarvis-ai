#!/usr/bin/env python3
from pathlib import Path
import ast, sys
ROOT = Path(__file__).resolve().parents[2]

def check(condition, label):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1

def main():
    failures = 0
    required = ["core/integration/__init__.py", "core/integration/bus.py", "core/integration/readiness.py",
        "core/src/routes/operations.py", "tests/test_genesis_vi_a3a_certification_repair.py",
        "dev/verify_genesis_vi_a3a_certification_repair.sh"]
    failures += check(all((ROOT / p).is_file() for p in required), "Canonical VI-A3A file set")
    parse_ok = True
    for p in required:
        if p.endswith('.py'):
            try: ast.parse((ROOT / p).read_text(encoding='utf-8'))
            except Exception as exc:
                parse_ok = False; print(f"[DETAIL] {p}: {exc}")
    failures += check(parse_ok, "Python syntax structure")
    init_text = (ROOT / "core/integration/__init__.py").read_text(encoding='utf-8')
    failures += check("_export_public" in init_text, "Existing public exports preserved")
    route_text = (ROOT / "core/src/routes/operations.py").read_text(encoding='utf-8')
    failures += check('@router.get("/capabilities")' in route_text, "Legacy capabilities route preserved")
    failures += check('@router.get("/bridge")' in route_text and '@router.get("/bridge/readiness")' in route_text,
        "Bridge routes installed additively")
    print('-' * 72); print(f"Checks failed : {failures}"); print("Overall status:", "EXCELLENT" if failures == 0 else "FAILED"); print('=' * 72)
    return 0 if failures == 0 else 1
if __name__ == '__main__': sys.exit(main())

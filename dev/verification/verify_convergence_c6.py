#!/usr/bin/env python3
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/observability/__init__.py",
    "core/observability/contracts.py",
    "core/observability/service.py",
    "core/conversation/orchestrator.py",
    "core/src/routes/operations.py",
    "tests/test_convergence_c6_executive_observability.py",
)

checks = []
def check(label, condition):
    checks.append(bool(condition)); print(f"[{'PASS' if condition else 'FAIL'}] {label}")

check("Canonical C-6 file set", all((ROOT / item).is_file() for item in REQUIRED))
try:
    for item in REQUIRED:
        if item.endswith('.py'): py_compile.compile(str(ROOT/item), doraise=True)
    check("Python compilation contract", True)
except Exception as exc:
    print(exc); check("Python compilation contract", False)

orch=(ROOT/'core/conversation/orchestrator.py').read_text()
routes=(ROOT/'core/src/routes/operations.py').read_text()
check("Executive orchestration publishes transparency", 'mission_transparency' in orch and 'observability_service.project' in orch)
check("Operations transparency route", '@router.get("/transparency")' in routes)
print("-"*72); print(f"Checks failed : {checks.count(False)}"); print("Overall status:", "EXCELLENT" if all(checks) else "FAILED")
sys.exit(0 if all(checks) else 1)

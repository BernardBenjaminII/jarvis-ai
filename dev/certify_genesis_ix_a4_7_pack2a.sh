#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

"${PYTHON_BIN}" - <<'PY'
from core.knowledge_catalog.qualified_search import (
    clear_last_qualification_state,
    get_last_qualification_result,
    get_last_qualification_trace,
    qualify_rows,
)

clear_last_qualification_state()

rows, result = qualify_rows(
    "internal architecture of the Quantum Banana Warp Core Mk XII",
    [
        {
            "file_path": "/knowledge/electronics.txt",
            "title": "Practical Electronics Handbook",
            "subject": "computer architecture",
            "excerpt": "Von Neumann architecture and electronics.",
            "confidence": 0.08,
        }
    ],
)

retained = get_last_qualification_result()
trace = get_last_qualification_trace()

assert retained is result
assert rows == []
assert trace is not None
assert trace["accepted_count"] == 0
assert trace["rejected_count"] == 1

clear_last_qualification_state()

assert get_last_qualification_result() is None
assert get_last_qualification_trace() is None

print("[PASS] Canonical qualified search runtime")
print("[PASS] QualificationResult retained")
print("[PASS] Qualification trace retained")
print("[PASS] Backward-compatible row projection")
print("[PASS] Request-local state clear operation")
PY

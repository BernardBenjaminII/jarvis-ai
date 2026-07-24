#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"

echo "======================================================================"
echo "JARVIS GENESIS III-F1 — COGNITIVE WORKSPACE INTEGRATION FREEZE"
echo "======================================================================"

if [[ -x dev/verify_genesis_3a4.sh ]]; then
  PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_3a4.sh >/dev/null
  printf '[PASS] Genesis III-A1 through III-A4 regression\n'
else
  printf '[FAIL] Missing Genesis III-A4 verifier\n' >&2
  exit 1
fi

"$PYTHON_BIN" -m py_compile \
  dev/tools/audit_genesis_3f1.py \
  dev/verification/verify_genesis_3f1.py \
  tests/test_genesis_3f1_integration_freeze.py
printf '[PASS] Genesis III-F1 package compilation\n'

"$PYTHON_BIN" dev/verification/verify_genesis_3f1.py
"$PYTHON_BIN" dev/tools/audit_genesis_3f1.py --check
printf '[PASS] Public API, dependency graph, and snapshot baselines are current\n'

"$PYTHON_BIN" -m unittest -v tests.test_genesis_3f1_integration_freeze
printf '[PASS] Genesis III-F1 constitutional tests\n'

"$PYTHON_BIN" - <<'PY'
from core.cognition import workspace
from core.cognition import integration
assert workspace is not None
assert integration is not None
print('[PASS] Canonical Genesis III package imports')
PY

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"

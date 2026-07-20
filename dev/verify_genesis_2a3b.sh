#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

PASSED=0
FAILED=0
pass(){ PASSED=$((PASSED+1)); echo "[PASS] $1"; }
fail(){ FAILED=$((FAILED+1)); echo "[FAIL] $1"; }
check(){ local d="$1"; shift; if "$@"; then pass "$d"; else fail "$d"; fi; }

echo "======================================================================"
echo "JARVIS GENESIS II-A3B — C1 VERIFICATION"
echo "======================================================================"

check "Validator compiles" \
  "${PYTHON_BIN}" -m py_compile dev/verification/genesis_manifest.py

check "Unit tests pass" \
  "${PYTHON_BIN}" -m unittest tests.test_genesis_2a3b_manifest_evolution

check "Manifest validates" \
  "${PYTHON_BIN}" dev/verification/genesis_manifest.py --check

check "Future extension remains possible" \
"${PYTHON_BIN}" - <<'PY'
from dev.verification.genesis_manifest import read_manifest_entries, validate_entries

entries=list(read_manifest_entries())

candidate="dev/verify_genesis_99z999.sh"
while candidate in entries:
    candidate="dev/verify_genesis_99z999a.sh"

report=validate_entries((*entries,candidate))
assert report.extension_count>=3
PY

echo "----------------------------------------------------------------------"
echo "Checks passed : ${PASSED}"
echo "Checks failed : ${FAILED}"
if [[ $FAILED -eq 0 ]]; then
 echo "Overall status: EXCELLENT"
 exit 0
fi
echo "Overall status: FAILED"
exit 1

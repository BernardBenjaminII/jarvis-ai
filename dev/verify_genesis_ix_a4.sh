#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check() {
  local label="$1"; shift
  if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1))
  else echo "[FAIL] ${label}"; failed=$((failed+1)); fi
}
echo "========================================================================"
echo "JARVIS — GENESIS IX-A4"
echo "RETRIEVAL ARCHITECTURE AUDIT & INTEGRATION READINESS"
echo "========================================================================"
run_check "IX-A4 compilation" \
  "${PYTHON_BIN}" -m py_compile \
  dev/audits/audit_genesis_ix_a4_retrieval_architecture.py \
  tests/test_genesis_ix_a4_retrieval_architecture_audit.py
run_check "IX-A4 audit tests" \
  "${PYTHON_BIN}" -m unittest -v \
  tests.test_genesis_ix_a4_retrieval_architecture_audit
run_check "Live retrieval audit" \
  env PYTHON_BIN="${PYTHON_BIN}" ./dev/audit_genesis_ix_a4.sh
run_check "Markdown report" \
  test -s docs/audits/genesis_ix_a4_retrieval_architecture.md
run_check "JSON report" \
  test -s docs/audits/genesis_ix_a4_retrieval_architecture.json
run_check "IX-A3 regression" \
  env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a3.sh
run_check "Architecture charter" \
  test -s docs/architecture/genesis_ix_a4_retrieval_architecture_audit.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]

#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$PROJECT_ROOT"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; passed=$((passed+1)); else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo '========================================================================'
echo 'JARVIS — GENESIS VII-C0A-1 ORGANIZATIONAL CONSTITUTION AUDIT'
echo '========================================================================'
run_check 'Audit package compilation' "$PYTHON_BIN" -m py_compile dev/tools/audit_organizational_constitution.py tests/test_genesis_vii_c0a1_organizational_constitution_audit.py
run_check 'Audit unit tests' "$PYTHON_BIN" -m unittest -v tests.test_genesis_vii_c0a1_organizational_constitution_audit
run_check 'Repository audit executes' "$PYTHON_BIN" dev/tools/audit_organizational_constitution.py
run_check 'JSON report generated' test -s artifacts/audit/genesis_vii_c0a1_organizational_constitution.json
run_check 'Markdown report generated' test -s artifacts/audit/genesis_vii_c0a1_organizational_constitution.md
echo '------------------------------------------------------------------------'; echo "Checks passed : $passed"; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo 'Overall status: EXCELLENT' || echo 'Overall status: FAILED'; echo '========================================================================'; [[ $failed -eq 0 ]]

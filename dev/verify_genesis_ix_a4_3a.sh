#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A4.3A"
echo "CERTIFICATION FAILURE ANALYZER"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile   core/retrieval/failure_analysis/analyzer.py   dev/certification/certify_genesis_ix_a4_3a.py   tests/test_genesis_ix_a4_3a_failure_analyzer.py

run_check "Unit tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_3a_failure_analyzer
run_check "IX-A4.3 certification JSON exists" test -s docs/audits/genesis_ix_a4_3/end_to_end_certification.json
run_check "Failure analysis" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_3a.sh

for report in failure_analysis.json failure_analysis.md failure_classification_matrix.md minimal_repair_plan.md
do
  run_check "Report ${report}" test -s "docs/audits/genesis_ix_a4_3a/${report}"
done

run_check "IX-A4.2A regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_2a.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a4_3a_certification_failure_analyzer.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A4.5 PACK 3A.2"
echo "NATIVE SEMANTIC FIXTURE INTEGRATION"
echo "========================================================================"

run_check "Repair module compilation" "${PYTHON_BIN}" -m py_compile   dev/certification/repair_genesis_ix_a4_5_pack3a_2.py   tests/test_genesis_ix_a4_5_pack3a_2_native_fixture.py

run_check "Apply native repair" "${PYTHON_BIN}" -m   dev.certification.repair_genesis_ix_a4_5_pack3a_2

run_check "Repaired source compilation" "${PYTHON_BIN}" -m py_compile   core/retrieval/certification/tracer.py   dev/certification/certify_genesis_ix_a4_3.py

run_check "Native fixture tests" "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a4_5_pack3a_2_native_fixture

run_check "End-to-end retrieval certification" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/certify_genesis_ix_a4_3.sh

run_check "Architecture document" test -s   docs/architecture/genesis_ix_a4_5_pack3a_2_native_semantic_fixture_integration.md

for report in native_fixture_repair.json native_fixture_repair.md
do
  run_check "Report ${report}" test -s     "docs/audits/genesis_ix_a4_5_pack3a_2/${report}"
done

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]

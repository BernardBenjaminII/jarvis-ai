#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A5 PACK 3R"
echo "RUNTIME QUALIFICATION FORENSICS"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile   dev/runtime_qualification_forensics/*.py   dev/run_genesis_ix_a5_pack3r_forensics.py   dev/certify_genesis_ix_a5_pack3r.py   tests/test_genesis_ix_a5_pack3r_forensics.py

run_check "Runtime forensic tests" "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a5_pack3r_forensics

run_check "Runtime forensic certification" "${PYTHON_BIN}" -m   dev.certify_genesis_ix_a5_pack3r

run_check "Live runtime forensic audit" "${PYTHON_BIN}" -m   dev.run_genesis_ix_a5_pack3r_forensics

run_check "Forensic JSON" test -s   docs/audits/genesis_ix_a5_pack3r/runtime_qualification_forensics.json

run_check "Forensic Markdown" test -s   docs/audits/genesis_ix_a5_pack3r/runtime_qualification_forensics.md

run_check "Architecture document" test -s   docs/architecture/genesis_ix_a5_pack3r_runtime_qualification_forensics.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]

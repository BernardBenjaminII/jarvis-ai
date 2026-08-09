#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
passed=0; failed=0
check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; passed=$((passed+1)); else echo "[FAIL] $label"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A5.8 PACK 1"
echo "CORPUS AUTHORITY AND MATERIALIZATION TRACE"
echo "========================================================================"
check "Compilation" "$PYTHON_BIN" -m py_compile dev/corpus_authority/*.py dev/run_genesis_ix_a5_8_pack1.py dev/certify_genesis_ix_a5_8_pack1.py tests/test_genesis_ix_a5_8_pack1.py
check "Unit tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a5_8_pack1
check "Certification" "$PYTHON_BIN" -m dev.certify_genesis_ix_a5_8_pack1
check "Live audit" "$PYTHON_BIN" -m dev.run_genesis_ix_a5_8_pack1
for f in corpus_authority.json authority_resolution.md materialization_pipeline.md corpus_dropoff.md executive_findings.md lineage_edges.json; do
  check "Artifact $f" test -s "docs/audits/genesis_ix_a5_8_pack1/$f"
done
check "Architecture" test -s docs/architecture/genesis_ix_a5_8_pack1_corpus_authority_trace.md
echo "------------------------------------------------------------------------"
echo "Checks passed : $passed"
echo "Checks failed : $failed"
[[ $failed -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ $failed -eq 0 ]]

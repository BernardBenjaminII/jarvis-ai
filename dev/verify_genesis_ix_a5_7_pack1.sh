#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
passed=0; failed=0
check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; passed=$((passed+1)); else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo "========================================================================"
echo "GENESIS IX-A5.7 PACK 1 — CORPUS INTELLIGENCE FRAMEWORK"
echo "========================================================================"
check "Compilation" "$PYTHON_BIN" -m py_compile dev/intelligence/*.py dev/run_genesis_ix_a5_7_pack1.py dev/certify_genesis_ix_a5_7_pack1.py tests/test_genesis_ix_a5_7_pack1.py
check "Tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a5_7_pack1
check "Certification" "$PYTHON_BIN" -m dev.certify_genesis_ix_a5_7_pack1
check "Live inventory" "$PYTHON_BIN" -m dev.run_genesis_ix_a5_7_pack1
for f in corpus_inventory.json database_candidates.md corpus_inventory.md database_inventory.md table_inventory.md runtime_inventory.md corpus_relationships.md relationship_graph.json; do
  check "Artifact $f" test -s "docs/audits/genesis_ix_a5_7_pack1/$f"
done
check "Architecture" test -s docs/architecture/genesis_ix_a5_7_pack1_corpus_intelligence.md
echo "------------------------------------------------------------------------"
echo "Checks passed : $passed"; echo "Checks failed : $failed"
[[ $failed -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ $failed -eq 0 ]]

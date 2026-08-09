#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$ROOT"; passed=0; failed=0
run(){ local l="$1"; shift; if "$@"; then echo "[PASS] $l"; passed=$((passed+1)); else echo "[FAIL] $l"; failed=$((failed+1)); fi; }
echo ========================================================================; echo 'GENESIS IX-A5.5 KNOWLEDGE CENSUS'; echo ========================================================================
run Compilation "$PYTHON_BIN" -m py_compile dev/knowledge_census/*.py dev/run_genesis_ix_a5_5_census.py dev/certify_genesis_ix_a5_5.py tests/test_genesis_ix_a5_5_knowledge_census.py
run Tests "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a5_5_knowledge_census
run Certification "$PYTHON_BIN" -m dev.certify_genesis_ix_a5_5
run 'Live census' "$PYTHON_BIN" -m dev.run_genesis_ix_a5_5_census
for f in census.json database_inventory.md schema_inventory.md metadata_inventory.md retrieval_inventory.md executive_compatibility.md reconstruction_recommendations.md; do run "Artifact $f" test -s "docs/audits/genesis_ix_a5_5/$f"; done
run Architecture test -s docs/architecture/genesis_ix_a5_5_knowledge_census.md
echo ------------------------------------------------------------------------; echo "Checks passed : $passed"; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo 'Overall Status : EXCELLENT' || echo 'Overall Status : FAILED'; echo ========================================================================; [[ $failed -eq 0 ]]

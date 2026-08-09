#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
passed=0; failed=0
check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; passed=$((passed+1)); else echo "[FAIL] $label"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A5.8 PACK 2"
echo "MATERIALIZER ELIGIBILITY AND CANDIDATE SELECTION AUDIT"
echo "========================================================================"
check "Compilation" "$PYTHON_BIN" -m py_compile dev/materializer_eligibility/*.py dev/run_genesis_ix_a5_8_pack2.py dev/certify_genesis_ix_a5_8_pack2.py tests/test_genesis_ix_a5_8_pack2.py
check "Unit tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a5_8_pack2
check "Certification" "$PYTHON_BIN" -m dev.certify_genesis_ix_a5_8_pack2
check "Live audit" "$PYTHON_BIN" -m dev.run_genesis_ix_a5_8_pack2
for f in materializer_eligibility.json eligibility_summary.md materializer_implementation.md authority_map.md candidate_dispositions.md; do
  check "Artifact $f" test -s "docs/audits/genesis_ix_a5_8_pack2/$f"
done
check "Architecture" test -s docs/architecture/genesis_ix_a5_8_pack2_materializer_eligibility.md
echo "------------------------------------------------------------------------"
echo "Checks passed : $passed"
echo "Checks failed : $failed"
[[ $failed -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ $failed -eq 0 ]]

#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }
echo "========================================================================"
echo "JARVIS — GENESIS IX-A3"
echo "RUNTIME KNOWLEDGE MATERIALIZATION"
echo "========================================================================"
run_check "IX-A3 package compilation" "$PYTHON_BIN" -m py_compile core/knowledge_catalog/materialization/contracts.py core/knowledge_catalog/materialization/engine.py core/knowledge_catalog/materialization/search.py core/knowledge_catalog/materialization/cli.py tests/test_genesis_ix_a3_runtime_knowledge_materialization.py
run_check "IX-A3 materialization tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a3_runtime_knowledge_materialization
run_check "Runtime search integrated" grep -q "search_runtime_knowledge" core/knowledge_catalog/search.py
run_check "Grounding preserves excerpts" grep -q "excerpt" core/conversation/grounding.py
run_check "IX-A2 regression" env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ix_a2.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a3_runtime_knowledge_materialization.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"; echo "Checks failed : ${failed}"
[[ $failed -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
[[ $failed -eq 0 ]]

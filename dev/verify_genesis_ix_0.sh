#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$PROJECT_ROOT"
passed=0; failed=0
run(){ local l="$1"; shift; if "$@"; then echo "[PASS] $l"; passed=$((passed+1)); else echo "[FAIL] $l"; failed=$((failed+1)); fi; }
echo '========================================================================'; echo 'JARVIS — GENESIS IX-0'; echo 'JARVIS OPERATIONAL INTEGRATION'; echo '========================================================================'
run 'VIII-B0 prerequisite' env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_viii_b0.sh
run 'Operational runtime compilation' "$PYTHON_BIN" -m compileall -q core/operational
run 'Operational integration tests' "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_0_jarvis_operational_integration
run 'Executable boot and heartbeat' env PYTHON_BIN="$PYTHON_BIN" ./dev/run_jarvis_operational.sh --heartbeat .01 --cycles 2
run 'Live state artifact generated' test -s artifacts/runtime/jarvis_operational_state.json
run 'Runtime command executes' env PYTHON_BIN="$PYTHON_BIN" ./dev/run_jarvis_operational.sh --heartbeat .01 --command show_health
run 'Architecture document exists' test -s docs/architecture/genesis_ix_0_jarvis_operational_integration.md
echo '------------------------------------------------------------------------'; echo "Checks passed : $passed"; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo 'Overall status: EXCELLENT' || echo 'Overall status: FAILED'; echo '========================================================================'; [[ $failed -eq 0 ]]

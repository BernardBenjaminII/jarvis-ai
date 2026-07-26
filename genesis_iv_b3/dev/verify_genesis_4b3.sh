#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
echo "========================================================================"
echo "JARVIS — GENESIS IV-B3 CANONICAL OBSERVATION CONVERGENCE"
echo "========================================================================"
"$PYTHON_BIN" -m py_compile core/observation/*.py tests/test_genesis_iv_b3_canonical_observation_convergence.py dev/verification/verify_genesis_iv_b3.py
echo "[PASS] Python compilation"
"$PYTHON_BIN" -m unittest -v tests.test_genesis_iv_b3_canonical_observation_convergence
"$PYTHON_BIN" dev/verification/verify_genesis_iv_b3.py
if [[ -f tests/test_genesis_iv_a1_executive_observation_bus.py ]]; then
  "$PYTHON_BIN" -m unittest -v tests.test_genesis_iv_a1_executive_observation_bus
  echo "[PASS] Genesis IV-A1 regression"
fi
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"

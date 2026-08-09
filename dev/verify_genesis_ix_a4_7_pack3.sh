#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$ROOT"
p=0; f=0
run(){ local l="$1";shift;if "$@";then echo "[PASS] $l";p=$((p+1));else echo "[FAIL] $l";f=$((f+1));fi;}
echo "========================================================================"; echo "GENESIS IX-A4.7 PACK 3"; echo "EXECUTIVE TRANSPARENCY & GROUNDED ANSWER TELEMETRY"; echo "========================================================================"
run "Compilation" "$PYTHON_BIN" -m py_compile core/conversation/grounded_answer/telemetry.py core/conversation/grounded_answer/integration.py dev/certification/repair_genesis_ix_a4_7_pack3.py tests/test_genesis_ix_a4_7_pack3_telemetry.py
run "Telemetry tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a4_7_pack3_telemetry
run "Apply integration" "$PYTHON_BIN" -m dev.certification.repair_genesis_ix_a4_7_pack3
run "Operations compilation" "$PYTHON_BIN" -m py_compile core/src/routes/operations.py
run "Live certification" env PYTHON_BIN="$PYTHON_BIN" ./dev/certify_genesis_ix_a4_7_pack3.sh
run "Pack 2B regression" env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ix_a4_7_pack2b.sh
run "Mission Control asset" test -s core/src/static/mission_control/grounded_answer_projection.js
run "Mission Control registration" grep -q grounded_answer_projection.js core/src/static/mission_control/index.html
run "Architecture document" test -s docs/architecture/genesis_ix_a4_7_pack3_transparency_telemetry.md
run "JSON report" test -s docs/audits/genesis_ix_a4_7_pack3/transparency_integration.json
run "Markdown report" test -s docs/audits/genesis_ix_a4_7_pack3/transparency_integration.md
echo "------------------------------------------------------------------------";echo "Checks passed : $p";echo "Checks failed : $f";[[ $f -eq 0 ]]&&echo "Overall Status : EXCELLENT"||echo "Overall Status : FAILED";echo "========================================================================";[[ $f -eq 0 ]]

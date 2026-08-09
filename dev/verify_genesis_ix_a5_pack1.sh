#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$ROOT"
echo "========================================================================"; echo "GENESIS IX-A5 PACK 1"; echo "KNOWLEDGE SUBSTRATE RETRIEVAL AUDIT"; echo "========================================================================"
"$PYTHON_BIN" -m py_compile dev/knowledge_audit/*.py dev/run_genesis_ix_a5_pack1_audit.py tests/test_genesis_ix_a5_pack1_retrieval_audit.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a5_pack1_retrieval_audit
"$PYTHON_BIN" dev/run_genesis_ix_a5_pack1_audit.py
test -s docs/audits/genesis_ix_a5_pack1/retrieval_audit.json
test -s docs/audits/genesis_ix_a5_pack1/retrieval_audit.md
env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ix_a4_8_pack2.sh
echo "Overall Status : EXCELLENT"; echo "========================================================================"

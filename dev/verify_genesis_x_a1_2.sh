#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
"$PYTHON_BIN" -m py_compile core/knowledge_catalog/production_materialization/pipeline.py \
 core/knowledge_catalog/production_materialization/writer_batch.py \
 core/knowledge_catalog/production_materialization/telemetry.py \
 dev/run_genesis_x_a1_2.py dev/certify_genesis_x_a1_2.py tests/test_genesis_x_a1_2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a1_2
"$PYTHON_BIN" -m dev.certify_genesis_x_a1_2
"$PYTHON_BIN" -m dev.run_genesis_x_a1_2 --help >/dev/null
echo "[PASS] Genesis X-A1.2 verification"

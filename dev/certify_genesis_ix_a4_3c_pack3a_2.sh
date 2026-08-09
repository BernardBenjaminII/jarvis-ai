#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"

"${PYTHON_BIN}" -m dev.certification.repair_genesis_ix_a4_3c_ast
"${PYTHON_BIN}" -m py_compile   core/runtime/source_analysis.py   core/retrieval/call_graph/reconstructor.py

exec env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_3c.sh

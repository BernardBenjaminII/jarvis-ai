#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

"${PYTHON_BIN}" -m \
  dev.certification.repair_genesis_ix_a4_4_runtime_integration

"${PYTHON_BIN}" -m py_compile \
  core/executive/director_dispatch.py \
  core/retrieval/gap_trace/tracer.py

exec env PYTHON_BIN="${PYTHON_BIN}" \
  ./dev/certify_genesis_ix_a4_3b.sh

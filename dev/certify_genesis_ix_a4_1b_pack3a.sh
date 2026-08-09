#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

exec "${PYTHON_BIN}" \
  dev/certification/certify_genesis_ix_a4_1b_pack3a_runtime.py \
  --root "${ROOT}" \
  "$@"

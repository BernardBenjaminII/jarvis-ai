#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

exec "${PYTHON_BIN}" \
  dev/audits/generate_genesis_ix_a4_1b_pack2_reports.py \
  "$@"

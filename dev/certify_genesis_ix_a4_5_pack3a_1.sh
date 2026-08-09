#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

"${PYTHON_BIN}" -m \
  dev.certification.repair_genesis_ix_a4_5_pack3a_1

exec env PYTHON_BIN="${PYTHON_BIN}" \
  ./dev/certify_genesis_ix_a4_3.sh

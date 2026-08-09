#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

exec "${PYTHON_BIN}" -m \
  dev.certification.certify_runtime_bootstrap \
  --root "${ROOT}" \
  "$@"

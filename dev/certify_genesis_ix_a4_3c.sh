#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
exec "${PYTHON_BIN}" -m dev.certification.certify_genesis_ix_a4_3c --root "${ROOT}" "$@"

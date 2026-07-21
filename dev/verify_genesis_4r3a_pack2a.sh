#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "Running Genesis IV-R3A Pack 2A verification..."
echo "Python: ${PYTHON_BIN}"
echo

"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack2a.py

#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-R0-A — REPOSITORY SKELETON VERIFICATION"
echo "======================================================================"
echo
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo

"${PYTHON_BIN}" -m compileall -q core/cognition

"${PYTHON_BIN}" \
    dev/verification/verify_genesis_4r0a_repository_skeleton.py

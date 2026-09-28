#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VII-A4 DURABLE ADMISSION WORKFLOW'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/acquisition/intake/__init__.py \
    knowledge_engine/acquisition/intake/models.py \
    knowledge_engine/acquisition/intake/service.py \
    dev/tests/acquisition/test_phase_7a4.py

"${PYTHON_BIN}" \
    -m dev.tests.acquisition.test_phase_7a4

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

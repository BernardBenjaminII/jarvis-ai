#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VII-A6 ASSIMILATION HANDOFF'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/acquisition/handoff/__init__.py \
    knowledge_engine/acquisition/handoff/identity.py \
    knowledge_engine/acquisition/handoff/models.py \
    knowledge_engine/acquisition/handoff/schema.py \
    knowledge_engine/acquisition/handoff/repository.py \
    knowledge_engine/acquisition/handoff/service.py \
    dev/tests/acquisition/test_phase_7a6.py

"${PYTHON_BIN}" \
    -m dev.tests.acquisition.test_phase_7a6

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

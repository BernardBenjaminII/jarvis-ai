#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VII-A5 ACQUISITION MISSIONS'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/acquisition/missions/__init__.py \
    knowledge_engine/acquisition/missions/identity.py \
    knowledge_engine/acquisition/missions/models.py \
    knowledge_engine/acquisition/missions/schema.py \
    knowledge_engine/acquisition/missions/repository.py \
    knowledge_engine/acquisition/missions/service.py \
    dev/tests/acquisition/test_phase_7a5.py

"${PYTHON_BIN}" \
    -m dev.tests.acquisition.test_phase_7a5

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-E4 EXTRACTION AND CHUNKING SERVICE'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/__init__.py \
    knowledge_engine/assimilation/runner.py \
    knowledge_engine/assimilation/services/__init__.py \
    knowledge_engine/assimilation/services/attempts.py \
    knowledge_engine/assimilation/services/extraction.py \
    knowledge_engine/assimilation/services/persistence.py \
    knowledge_engine/assimilation/services/state.py \
    dev/tests/test_phase_6e4.py

"${PYTHON_BIN}" -m dev.tests.test_phase_6e4

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

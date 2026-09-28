#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VII-A1 ACQUISITION FOUNDATION'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/acquisition/__init__.py \
    knowledge_engine/acquisition/models.py \
    knowledge_engine/acquisition/provider_registry.py \
    knowledge_engine/acquisition/director.py \
    knowledge_engine/acquisition/providers/__init__.py \
    knowledge_engine/acquisition/providers/base.py \
    knowledge_engine/acquisition/providers/filesystem.py \
    dev/tests/test_phase_7a1.py

"${PYTHON_BIN}" -m dev.tests.test_phase_7a1

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

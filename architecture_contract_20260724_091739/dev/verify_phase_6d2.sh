#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-D2 COLLECTION EXPANSION PLANNING'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/__init__.py \
    knowledge_engine/assimilation/collection_plan.py \
    knowledge_engine/assimilation/dispatch.py \
    knowledge_engine/assimilation/handler_registry.py \
    knowledge_engine/assimilation/registry_builder.py \
    knowledge_engine/assimilation/handlers/__init__.py \
    knowledge_engine/assimilation/handlers/base.py \
    knowledge_engine/assimilation/handlers/single_document.py \
    knowledge_engine/assimilation/handlers/source_collection.py \
    knowledge_engine/assimilation/director.py \
    dev/tests/test_phase_6d2.py

"${PYTHON_BIN}" -m dev.tests.test_phase_6d2

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'

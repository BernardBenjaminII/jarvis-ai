#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VI-F2 ARCHITECTURE CONTRACTS"
echo "======================================================================"

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/repositories/knowledge_registry.py \
    knowledge_engine/assimilation/handlers/source_collection.py \
    dev/tests/test_registry_repository.py \
    dev/tests/test_services_api.py \
    dev/tests/test_architecture_contracts.py

"${PYTHON_BIN}" -m dev.tests.test_registry_repository
"${PYTHON_BIN}" -m dev.tests.test_services_api
"${PYTHON_BIN}" -m dev.tests.test_architecture_contracts

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"

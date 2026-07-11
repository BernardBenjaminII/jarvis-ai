#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
CATALOG_DB="${JARVIS_CATALOG_DB:-/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite}"
REPORT_DIR="${REPO_ROOT}/artifacts/phase_vi"
PLAN_REPORT="${REPORT_DIR}/object_dispatch_plan.json"
INVENTORY_REPORT="${REPORT_DIR}/object_dispatch_inventory.json"

PASSED=0
FAILED=0

pass() {
    PASSED=$((PASSED + 1))
    printf '[PASS] %s\n' "$1"
}

fail() {
    FAILED=$((FAILED + 1))
    printf '[FAIL] %s\n' "$1" >&2
}

run_check() {
    local description="$1"
    shift

    if "$@"; then
        pass "${description}"
    else
        fail "${description}"
    fi
}

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-A2 DISPATCH VERIFICATION'
printf '%s\n' '======================================================================'
printf 'Repository : %s\n' "${REPO_ROOT}"
printf 'Python     : %s\n' "${PYTHON_BIN}"
printf 'Catalog    : %s\n' "${CATALOG_DB}"
printf '%s\n' '----------------------------------------------------------------------'

run_check \
    'Assimilation package compiles' \
    "${PYTHON_BIN}" -m py_compile \
        knowledge_engine/assimilation/__init__.py \
        knowledge_engine/assimilation/dispatch.py \
        knowledge_engine/assimilation/mission.py \
        knowledge_engine/assimilation/planner.py \
        knowledge_engine/assimilation/director.py \
        knowledge_engine/assimilation/runner.py \
        knowledge_engine/assimilation/single_document.py \
        knowledge_engine/assimilation_cli.py

run_check \
    'Director and dispatch imports work' \
    "${PYTHON_BIN}" -c \
        'from knowledge_engine.assimilation import AssimilationDirector, get_handler_spec; assert get_handler_spec("single_document").handler_name == "document_assimilation"; print("Imports OK")'

run_check \
    'CLI help works' \
    "${PYTHON_BIN}" -m knowledge_engine.assimilation_cli --help

mkdir -p "${REPORT_DIR}"

run_check \
    'Registry inventory succeeds' \
    "${PYTHON_BIN}" -m knowledge_engine.assimilation_cli \
        --db "${CATALOG_DB}" \
        --inventory \
        --json \
        --output "${INVENTORY_REPORT}"

run_check \
    'Object-type-aware plan succeeds' \
    "${PYTHON_BIN}" -m knowledge_engine.assimilation_cli \
        --db "${CATALOG_DB}" \
        --plan \
        --limit 25 \
        --json \
        --output "${PLAN_REPORT}"

if [[ -s "${PLAN_REPORT}" ]] && \
   "${PYTHON_BIN}" -m json.tool "${PLAN_REPORT}" >/dev/null
then
    pass 'Mission plan JSON is valid'
else
    fail 'Mission plan JSON is invalid'
fi

if [[ -s "${INVENTORY_REPORT}" ]] && \
   "${PYTHON_BIN}" -m json.tool "${INVENTORY_REPORT}" >/dev/null
then
    pass 'Inventory JSON is valid'
else
    fail 'Inventory JSON is invalid'
fi

run_check \
    'Queued-work state selection is correct' \
    "${PYTHON_BIN}" - <<PY
import json
from pathlib import Path

payload = json.loads(
    Path("${PLAN_REPORT}").read_text(encoding="utf-8")
)

assert payload["status"] == "planned"
assert payload["summary"]["total_items"] > 0

for item in payload["items"]:
    assert item["assimilation_state"] == "queued"
    assert item["handler_name"]
    assert item["handler_readiness"] in {
        "available",
        "planned",
        "unsupported",
    }

print("Queued-work planning checks OK")
PY

run_check \
    'Execution lock is active' \
    "${PYTHON_BIN}" - <<PY
from knowledge_engine.assimilation import (
    AssimilationDirector,
    AssimilationExecutionLockedError,
)
from knowledge_engine.storage.database import KnowledgeDatabase

db = KnowledgeDatabase("${CATALOG_DB}")
director = AssimilationDirector(db)
mission = director.plan(limit=1)

try:
    director.execute(mission)
except AssimilationExecutionLockedError:
    print("Execution lock confirmed")
else:
    raise AssertionError("Execution unexpectedly proceeded")
PY

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${PASSED}"
printf 'Checks failed : %d\n' "${FAILED}"

if (( FAILED == 0 )); then
    printf '%s\n' 'Overall status: EXCELLENT'
    printf '%s\n' '======================================================================'
    exit 0
fi

printf '%s\n' 'Overall status: ATTENTION REQUIRED'
printf '%s\n' '======================================================================'
exit 1

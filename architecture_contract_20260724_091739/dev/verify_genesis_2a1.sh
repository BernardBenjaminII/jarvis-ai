#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    printf '[PASS] %s\n' "$1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

run_check() {
    local description="$1"
    shift

    if "$@"; then
        pass "$description"
    else
        fail "$description"
    fi
}

printf '\n'
printf '======================================================================\n'
printf 'JARVIS GENESIS II-A1 — REASONING SESSION CONTRACT\n'
printf '======================================================================\n'

run_check \
    "Reasoning session package compilation" \
    "$PYTHON_BIN" -m compileall -q core/reasoning/session

run_check \
    "Stable reasoning session public imports" \
    "$PYTHON_BIN" -c \
    'from core.reasoning.session import ReasoningSession, ReasoningSessionId, ReasoningSessionMetadata, ReasoningSessionState, SessionAttribute'

run_check \
    "Genesis II-A1 contract tests" \
    "$PYTHON_BIN" -m pytest -q tests/test_genesis_2a1_reasoning_session_contract.py

run_check \
    "Certified ReasoningEngine remains importable" \
    "$PYTHON_BIN" -c \
    'from core.reasoning.service import ReasoningEngine'

run_check \
    "Session package does not import ReasoningEngine implementation" \
    "$PYTHON_BIN" -c '
import ast
from pathlib import Path

for path in Path("core/reasoning/session").glob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("core.reasoning.service"):
                    raise AssertionError(
                        f"{path}: forbidden import {alias.name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module == "core.reasoning.service":
                raise AssertionError(
                    f"{path}: forbidden import from {node.module}"
                )

print("OK")
'

run_check \
    "Session contracts contain no time, random, network, process, or persistence imports" \
    "$PYTHON_BIN" -c '
import ast
from pathlib import Path

blocked = {
    "datetime",
    "time",
    "random",
    "secrets",
    "socket",
    "requests",
    "httpx",
    "subprocess",
    "sqlite3",
}

tree = ast.parse(
    Path("core/reasoning/session/contracts.py").read_text(
        encoding="utf-8"
    )
)

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.add(alias.name.split(".")[0])

    elif isinstance(node, ast.ImportFrom):
        imports.add((node.module or "").split(".")[0])

forbidden = imports & blocked

assert not forbidden, forbidden

print("OK")
'

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "$PASS_COUNT"
printf 'Checks failed : %d\n' "$FAIL_COUNT"

if (( FAIL_COUNT == 0 )); then
    printf 'Overall status: EXCELLENT\n'
    printf '======================================================================\n'
    exit 0
fi

printf 'Overall status: FAILED\n'
printf '======================================================================\n'
exit 1

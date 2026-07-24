#!/usr/bin/env bash

set -u

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
    pwd
)"
PYTHON_BIN="${PYTHON_BIN:-python}"
PASSED=0
FAILED=0

cd "$PROJECT_ROOT" || exit 1

pass() {
    PASSED=$((PASSED + 1))
    printf '[PASS] %s\n' "$1"
}

fail() {
    FAILED=$((FAILED + 1))
    printf '[FAIL] %s\n' "$1"
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

printf '\n%s\n' '======================================================================'
printf '%s\n' 'JARVIS GENESIS II-A2R — CANONICAL REASONING FIXTURES'
printf '%s\n' '======================================================================'

run_check     "Canonical fixture package compilation"     "$PYTHON_BIN" -m compileall -q tests/fixtures

run_check     "Canonical fixture public imports"     "$PYTHON_BIN" - <<'PY'
from tests.fixtures.reasoning import (
    DEFAULT_CREATED_BY,
    DEFAULT_MATERIAL,
    DEFAULT_NAMESPACE,
    make_identifier,
    make_metadata,
    make_reasoning_session,
)

assert DEFAULT_CREATED_BY
assert DEFAULT_MATERIAL
assert DEFAULT_NAMESPACE
assert make_identifier
assert make_metadata
assert make_reasoning_session
PY

run_check     "Canonical reasoning fixture certification tests"     "$PYTHON_BIN" -m pytest -q tests/test_reasoning_fixtures.py

run_check     "Genesis II-A1 contract regression"     "$PYTHON_BIN" -m pytest -q     tests/test_genesis_2a1_reasoning_session_contract.py

run_check     "Fixtures depend only on certified public session contracts"     "$PYTHON_BIN" - <<'PY'
import ast
from pathlib import Path

path = Path("tests/fixtures/reasoning.py")
tree = ast.parse(path.read_text(encoding="utf-8"))
violations = []

for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if module.startswith("core.reasoning.session.") and module != "core.reasoning.session":
            violations.append(
                f"{path}:{node.lineno}: fixture imports internal module {module}"
            )

if violations:
    raise AssertionError("\n".join(violations))

print("OK")
PY

run_check     "Canonical fixtures documentation exists"     test -f tests/fixtures/README.md

run_check     "ADR-0018 exists"     test -f docs/decisions/ADR-0018.md

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %s\n' "$PASSED"
printf 'Checks failed : %s\n' "$FAILED"

if [ "$FAILED" -eq 0 ]; then
    printf '%s\n' 'Overall status: EXCELLENT'
    printf '%s\n' '======================================================================'
    exit 0
fi

printf '%s\n' 'Overall status: FAILED'
printf '%s\n' '======================================================================'
exit 1

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
printf '%s\n' 'JARVIS GENESIS II-A2 — REASONING SESSION LIFECYCLE'
printf '%s\n' '======================================================================'

run_check     "Genesis II-A2R canonical fixture certification"     env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_reasoning_fixtures.sh

run_check     "Reasoning session lifecycle package compilation"     "$PYTHON_BIN" -m compileall -q core/reasoning/session

run_check     "Stable Genesis II-A2 public imports"     "$PYTHON_BIN" - <<'PY'
from core.reasoning.session import (
    InvalidReasoningSessionTransitionError,
    LifecycleManager,
    ReasoningSessionLifecycle,
    TERMINAL_STATES,
    TRANSITION_MAP,
    TerminalReasoningSessionError,
)

assert LifecycleManager is ReasoningSessionLifecycle
assert TRANSITION_MAP
assert TERMINAL_STATES
assert issubclass(
    TerminalReasoningSessionError,
    InvalidReasoningSessionTransitionError,
)
PY

run_check     "Genesis II-A2 lifecycle tests"     "$PYTHON_BIN" -m pytest -q     tests/test_genesis_2a2_reasoning_session_lifecycle.py

run_check     "Certified ReasoningEngine remains importable"     "$PYTHON_BIN" - <<'PY'
from core.reasoning.service import ReasoningEngine
assert ReasoningEngine is not None
PY

run_check     "Every reasoning session state is lifecycle governed"     "$PYTHON_BIN" - <<'PY'
from core.reasoning.session import ReasoningSessionState, TRANSITION_MAP
assert set(TRANSITION_MAP) == set(ReasoningSessionState)
PY

run_check     "Terminal session states expose no legal successors"     "$PYTHON_BIN" - <<'PY'
from core.reasoning.session import TERMINAL_STATES, TRANSITION_MAP

for state in TERMINAL_STATES:
    assert TRANSITION_MAP[state] == frozenset()
PY

run_check     "Lifecycle package has no forbidden runtime imports"     "$PYTHON_BIN" - <<'PY'
import ast
from pathlib import Path

forbidden = {
    "asyncio",
    "datetime",
    "http",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "random",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "time",
    "urllib",
}
violations = []

for path in sorted(Path("core/reasoning/session").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in forbidden:
                    violations.append(
                        f"{path}:{node.lineno}: import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in forbidden:
                violations.append(
                    f"{path}:{node.lineno}: from {node.module} import ..."
                )

if violations:
    raise AssertionError("\n".join(violations))

print("OK")
PY

run_check     "Lifecycle does not import ReasoningEngine implementation"     "$PYTHON_BIN" - <<'PY'
import ast
from pathlib import Path

violations = []

for path in sorted(Path("core/reasoning/session").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core.reasoning.service":
                    violations.append(
                        f"{path}:{node.lineno}: import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "core.reasoning.service":
                violations.append(
                    f"{path}:{node.lineno}: "
                    "from core.reasoning.service import ..."
                )

if violations:
    raise AssertionError("\n".join(violations))

print("OK")
PY

run_check     "II-A2 tests use canonical fixtures"     "$PYTHON_BIN" - <<'PY'
from pathlib import Path

path = Path("tests/test_genesis_2a2_reasoning_session_lifecycle.py")
text = path.read_text(encoding="utf-8")

assert "from tests.fixtures.reasoning import make_reasoning_session" in text
assert "def _construct_identifier" not in text
assert "def _construct_metadata" not in text
assert "def _required_value" not in text
assert "def make_session" not in text
PY

run_check     "Genesis II-A2 architecture document exists"     test -f     docs/architecture/genesis/reasoning/GENESIS_II_A2_REASONING_SESSION_LIFECYCLE.md

run_check     "Genesis II-A2R architecture document exists"     test -f     docs/architecture/testing/CANONICAL_CONSTITUTIONAL_FIXTURES.md

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

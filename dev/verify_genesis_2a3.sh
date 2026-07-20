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
printf '%s\n' 'JARVIS GENESIS II-A3 — CONSTITUTIONAL REASONING CONTEXT'
printf '%s\n' '======================================================================'

run_check     "Genesis II-A3 package compilation"     "$PYTHON_BIN" -m compileall -q core/reasoning/context tests/fixtures

run_check     "Stable Genesis II-A3 public imports"     "$PYTHON_BIN" - <<'PY'
from core.reasoning.context import (
    ContextManager,
    DecisionCriterion,
    DuplicateReasoningContextKeyError,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextContractError,
    ReasoningContextError,
    ReasoningContextId,
    ReasoningContextManager,
)

assert ContextManager is ReasoningContextManager
assert issubclass(
    DuplicateReasoningContextKeyError,
    ReasoningContextContractError,
)
assert issubclass(ReasoningContextContractError, ReasoningContextError)
assert DecisionCriterion
assert OpenReasoningQuestion
assert ReasoningAssumption
assert ReasoningConstraint
assert ReasoningContext
assert ReasoningContextAttribute
assert ReasoningContextId
PY

run_check     "Genesis II-A3 canonical context fixture tests"     "$PYTHON_BIN" -m pytest -q     tests/test_reasoning_context_fixtures.py

run_check     "Genesis II-A3 constitutional context tests"     "$PYTHON_BIN" -m pytest -q     tests/test_genesis_2a3_reasoning_context.py

run_check     "Genesis II-A2R fixture regression"     env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_reasoning_fixtures.sh

run_check     "Genesis II-A2 lifecycle regression"     env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_2a2.sh

run_check     "Genesis II-A1 contract regression"     "$PYTHON_BIN" -m pytest -q     tests/test_genesis_2a1_reasoning_session_contract.py

run_check     "Context depends only on certified session public surface"     "$PYTHON_BIN" - <<'PY'
import ast
from pathlib import Path

violations = []

for path in sorted(Path("core/reasoning/context").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("core.reasoning.session."):
                violations.append(
                    f"{path}:{node.lineno}: imports private session module {module}"
                )

if violations:
    raise AssertionError("\n".join(violations))

print("OK")
PY

run_check     "Context package has no forbidden runtime imports"     "$PYTHON_BIN" - <<'PY'
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

for path in sorted(Path("core/reasoning/context").glob("*.py")):
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

run_check     "Context contracts remain immutable dataclasses"     "$PYTHON_BIN" - <<'PY'
from dataclasses import fields, is_dataclass

from core.reasoning.context import (
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextId,
)

contracts = (
    DecisionCriterion,
    OpenReasoningQuestion,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningContext,
    ReasoningContextAttribute,
    ReasoningContextId,
)

for contract in contracts:
    assert is_dataclass(contract)
    params = contract.__dataclass_params__
    assert params.frozen
    assert fields(contract)
PY

run_check     "Genesis II-A3 architecture document exists"     test -f     docs/architecture/genesis/reasoning/GENESIS_II_A3_CONSTITUTIONAL_REASONING_CONTEXT.md

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

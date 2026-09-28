#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT" || exit 1

PASS_COUNT=0
FAIL_COUNT=0

print_header() {
    printf '\n'
    printf '%s\n' \
        '======================================================================'
    printf '%s\n' \
        'JARVIS GEN 2 — PHASE IX-C2 PLANNING DATA MODEL'
    printf '%s\n' \
        '======================================================================'
}

pass_check() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail_check() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
}

run_check() {
    local description="$1"
    shift

    if "$@"; then
        pass_check "$description"
    else
        fail_check "$description"
    fi
}

print_header

run_check \
    "Executive planning package compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/executive/__init__.py \
        core/executive/planning/__init__.py \
        core/executive/planning/enums.py \
        core/executive/planning/errors.py \
        core/executive/planning/models.py \
        core/executive/planning/dependencies.py \
        core/executive/planning/validation.py \
        core/executive/planning/repository.py \
        core/executive/planning/service.py

run_check \
    "Stable planning public imports" \
    "$PYTHON_BIN" -c '
from core.executive.planning import (
    Activity,
    AuthorizationRequirement,
    Command,
    Dependency,
    DependencyGraph,
    InMemoryPlanRepository,
    Mission,
    MissionPlan,
    Objective,
    PlanningService,
    PlanState,
    PlanVersion,
    Task,
)
print("planning imports verified")
'

run_check \
    "Phase IX-C2 unit tests" \
    "$PYTHON_BIN" -m unittest \
        tests.test_phase_9c2_planning_data_model \
        -v

run_check \
    "Planning architecture document present" \
    test -f docs/architecture/13_mission_planning_architecture.md

run_check \
    "Canonical mission hierarchy documented" \
    grep -q \
        "Mission" \
        docs/architecture/13_mission_planning_architecture.md

run_check \
    "Canonical declaration documented" \
    grep -q \
        "^# 13. Canonical Declaration" \
        docs/architecture/13_mission_planning_architecture.md

run_check \
    "Deterministic dependency graph smoke test" \
    "$PYTHON_BIN" - <<'PY'
from core.executive.planning import Dependency, DependencyGraph

graph = DependencyGraph(
    element_ids=("a", "b", "c"),
    dependencies=(
        Dependency(
            dependency_id="d1",
            predecessor_id="a",
            successor_id="b",
        ),
        Dependency(
            dependency_id="d2",
            predecessor_id="b",
            successor_id="c",
        ),
    ),
)

assert graph.topological_order() == ("a", "b", "c")
print("dependency graph verified")
PY

run_check \
    "Immutable version fingerprint smoke test" \
    "$PYTHON_BIN" - <<'PY'
from core.executive.planning import (
    AuthorizationMode,
    AuthorizationRequirement,
    Mission,
    PlanState,
    create_plan_version,
)

mission = Mission(
    mission_id="mission-smoke",
    title="Planning fingerprint smoke test",
    commander_intent="Verify deterministic immutable plan fingerprints.",
    desired_end_state="A valid immutable version exists.",
    owner="commander",
    completion_criteria=("Fingerprint exists.",),
    authorization=AuthorizationRequirement(
        mode=AuthorizationMode.COMMANDER_APPROVAL,
        approving_authority="commander",
    ),
)

version = create_plan_version(
    mission=mission,
    state=PlanState.DRAFT,
    plan_id="plan-smoke",
)

assert len(version.fingerprint) == 64
assert version.calculate_fingerprint() == version.fingerprint
print(version.fingerprint)
PY

printf '%s\n' \
    '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "$PASS_COUNT"
printf 'Checks failed : %d\n' "$FAIL_COUNT"

if [ "$FAIL_COUNT" -eq 0 ]; then
    printf 'Overall status: EXCELLENT\n'
    printf '%s\n' \
        '======================================================================'
    exit 0
fi

printf 'Overall status: FAILED\n'
printf '%s\n' \
    '======================================================================'
exit 1

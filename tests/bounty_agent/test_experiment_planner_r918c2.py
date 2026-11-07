import pytest

from core.bounty_agent.autonomy.experiment_planner_r918c2 import (
    EXPERIMENTS,
    ExperimentPlanningError,
    select_next,
)
from core.bounty_agent.autonomy.hypothesis_engine_r918 import (
    CAPABILITIES,
)


BASELINE = {
    "capability": "baseline_http",
    "state": "completed",
    "valid_product_response": True,
    "product_ids": [1, 2, 3],
}

SYNTAX = {
    "capability": "sql_syntax_diagnostic",
    "state": "completed",
    "http_status": 500,
    "sqlite_error": "SQLite error observed",
}

VARIATION = {
    "capability": "boolean_comparison",
    "state": "completed",
    "valid_product_response": True,
    "product_ids": [1, 2, 3],
}

REPEAT = {
    "capability": "reproducibility_check",
    "state": "completed",
    "valid_product_response": True,
    "product_ids": [1, 2, 3],
}


def plan(history, budget=5, allowed=CAPABILITIES):
    return select_next(
        observations=history,
        allowed_capabilities=allowed,
        remaining_budget=budget,
    )


def test_initial_baseline():
    decision = plan([])
    assert decision.capability == "baseline_http"
    assert decision.execution_allowed is False


def test_baseline_to_syntax():
    assert plan([BASELINE]).capability == "sql_syntax_diagnostic"


def test_sql_signal_selects_variation():
    decision = plan([BASELINE, SYNTAX])
    assert decision.capability == "boolean_comparison"
    assert "syntax_condition_reproduction_missing" in (
        decision.evidence_gaps
    )


def test_variation_selects_baseline_repeat():
    decision = plan([BASELINE, SYNTAX, VARIATION])
    assert decision.capability == "reproducibility_check"


def test_complete_mission_stops():
    decision = plan([BASELINE, SYNTAX, VARIATION, REPEAT])
    assert decision.action == "stop"
    assert decision.capability is None
    assert "baseline_repetition_does_not_reproduce_sql_error" in (
        decision.evidence_gaps
    )


def test_no_sql_signal_stops_after_diagnostic():
    diagnostic = {
        "capability": "sql_syntax_diagnostic",
        "state": "completed",
        "http_status": 200,
        "sqlite_error": None,
    }
    assert plan([BASELINE, diagnostic]).action == "stop"


def test_failed_attempt_is_not_repeated():
    failed = {
        "capability": "sql_syntax_diagnostic",
        "state": "failed",
    }
    assert plan([BASELINE, failed]).action == "stop"


def test_budget_boundary():
    assert plan([], budget=0).action == "stop"


def test_capability_boundary():
    decision = plan(
        [BASELINE],
        allowed=frozenset({"baseline_http"}),
    )
    assert decision.action == "stop"


def test_experiment_identity():
    assert EXPERIMENTS[
        "reproducibility_check"
    ].repeats_identity == "baseline_apple"


@pytest.mark.parametrize("budget", [-1, True, 1.5])
def test_invalid_budget(budget):
    with pytest.raises(ExperimentPlanningError):
        plan([], budget=budget)


def test_duplicate_rejected():
    with pytest.raises(ExperimentPlanningError):
        plan([BASELINE, BASELINE])


def test_unknown_capability_rejected():
    with pytest.raises(ExperimentPlanningError):
        plan([{"capability": "arbitrary_command", "state": "completed"}])

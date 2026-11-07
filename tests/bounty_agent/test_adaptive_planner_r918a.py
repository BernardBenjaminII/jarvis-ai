import pytest

from core.bounty_agent.autonomy.adaptive_planner_r918 import (
    PlanningError,
    plan_next,
)

ALL = frozenset({
    "baseline_http",
    "sql_syntax_diagnostic",
    "boolean_comparison",
    "reproducibility_check",
})


@pytest.mark.parametrize(
    ("observations", "expected"),
    [
        ([], "baseline_http"),
        ([{"sqlite_error": "incomplete input"}],
         "sql_syntax_diagnostic"),
        ([{"baseline_complete": True}],
         "boolean_comparison"),
        ([{"behavioral_difference": True}],
         "reproducibility_check"),
        ([{"validated_local_lab": True}],
         "reproducibility_check"),
    ],
)
def test_adaptive_decisions(observations, expected):
    decision = plan_next(
        observations=observations,
        allowed_capabilities=ALL,
        remaining_budget=5,
    )
    assert decision.capability == expected
    assert decision.execution_allowed is False


def test_budget_exhaustion():
    decision = plan_next(
        observations=[],
        allowed_capabilities=ALL,
        remaining_budget=0,
    )
    assert decision.action == "stop"


def test_capability_boundary():
    decision = plan_next(
        observations=[{"sqlite_error": "incomplete input"}],
        allowed_capabilities=frozenset({"baseline_http"}),
        remaining_budget=5,
    )
    assert decision.action == "stop"


def test_unknown_capability_rejected():
    with pytest.raises(PlanningError):
        plan_next(
            observations=[],
            allowed_capabilities=frozenset({"arbitrary_shell"}),
            remaining_budget=5,
        )

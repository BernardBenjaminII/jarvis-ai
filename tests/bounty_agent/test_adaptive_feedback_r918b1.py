from core.bounty_agent.autonomy.adaptive_planner_r918 import (
    CAPABILITIES,
    plan_next,
)


SEQUENCE = (
    "baseline_http",
    "sql_syntax_diagnostic",
    "boolean_comparison",
    "reproducibility_check",
)


def observation(capability):
    return {
        "capability": capability,
        "state": "completed",
        "valid_product_response": True,
        "product_count": 3,
    }


def test_complete_history_progression():
    history = []

    for expected in SEQUENCE:
        remaining = CAPABILITIES - {
            item["capability"] for item in history
        }

        decision = plan_next(
            observations=history,
            allowed_capabilities=frozenset(remaining),
            remaining_budget=5 - len(history),
        )

        assert decision.action == "propose_test"
        assert decision.capability == expected
        assert decision.execution_allowed is False

        history.append(observation(expected))

    final = plan_next(
        observations=history,
        allowed_capabilities=frozenset(),
        remaining_budget=1,
    )

    assert final.action == "stop"
    assert final.rationale == "Investigation catalog completed"


def test_invalid_baseline_stops():
    history = [{
        "capability": "baseline_http",
        "state": "completed",
        "valid_product_response": False,
    }]

    decision = plan_next(
        observations=history,
        allowed_capabilities=CAPABILITIES,
        remaining_budget=4,
    )

    assert decision.action == "stop"


def test_completed_baseline_not_repeated():
    history = [
        observation("baseline_http"),
        observation("boolean_comparison"),
    ]

    decision = plan_next(
        observations=history,
        allowed_capabilities=frozenset({
            "sql_syntax_diagnostic",
            "reproducibility_check",
        }),
        remaining_budget=3,
    )

    assert decision.capability == "sql_syntax_diagnostic"
    assert decision.capability != "baseline_http"

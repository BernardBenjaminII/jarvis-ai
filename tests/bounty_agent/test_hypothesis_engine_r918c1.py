import pytest

from core.bounty_agent.autonomy.hypothesis_engine_r918 import (
    CAPABILITIES,
    HypothesisError,
    assess,
)


def observation(capability, **fields):
    return {
        "capability": capability,
        "state": "completed",
        **fields,
    }


BASELINE = observation(
    "baseline_http",
    http_status=200,
    valid_product_response=True,
    product_ids=[1, 2, 3],
)

SQL_ERROR = observation(
    "sql_syntax_diagnostic",
    http_status=500,
    sqlite_error="SQLite error observed",
)

COMPARISON = observation(
    "boolean_comparison",
    http_status=200,
    valid_product_response=True,
    product_ids=[1, 2, 3],
)

REPEAT = observation(
    "reproducibility_check",
    http_status=200,
    valid_product_response=True,
    product_ids=[1, 2, 3],
)


def evaluate(history, budget=5, allowed=CAPABILITIES):
    return assess(
        observations=history,
        allowed_capabilities=allowed,
        remaining_budget=budget,
    )


def test_empty_history_requests_baseline():
    result = evaluate([])
    assert result.next_capability == "baseline_http"
    assert result.execution_allowed is False


def test_baseline_requests_syntax_diagnostic():
    result = evaluate([BASELINE])
    assert result.next_capability == "sql_syntax_diagnostic"


def test_sql_error_requests_comparison():
    result = evaluate([BASELINE, SQL_ERROR])
    assert result.next_capability == "boolean_comparison"
    assert result.classification == "sql_diagnostic_signal"

    sql = result.hypotheses[0]
    assert sql.identifier == "sql_parser_interaction"
    assert sql.confidence == "supported"
    assert result.validated_vulnerability is False


def test_sql_signal_requests_reproducibility():
    result = evaluate([BASELINE, SQL_ERROR, COMPARISON])
    assert result.next_capability == "reproducibility_check"


def test_complete_history_stops():
    result = evaluate([
        BASELINE, SQL_ERROR, COMPARISON, REPEAT
    ])
    assert result.next_capability is None
    assert result.human_review_required is True
    assert result.validated_vulnerability is False


def test_generic_error_does_not_trigger_sql_comparison():
    generic = observation(
        "sql_syntax_diagnostic",
        http_status=500,
        sqlite_error=None,
    )
    result = evaluate([BASELINE, generic])
    assert result.next_capability is None
    assert result.classification == "inconclusive"


def test_invalid_baseline_stops():
    invalid = observation(
        "baseline_http",
        valid_product_response=False,
    )
    assert evaluate([invalid]).next_capability is None


def test_budget_exhaustion_stops():
    assert evaluate([BASELINE], budget=0).next_capability is None


def test_capability_boundary():
    result = evaluate(
        [BASELINE],
        allowed=frozenset({"baseline_http"}),
    )
    assert result.next_capability is None
    assert result.execution_allowed is False


@pytest.mark.parametrize("budget", [-1, True, 1.5])
def test_invalid_budget_rejected(budget):
    with pytest.raises(HypothesisError):
        evaluate([], budget=budget)


def test_unknown_capability_rejected():
    with pytest.raises(HypothesisError):
        evaluate([
            observation("arbitrary_shell")
        ])


def test_duplicate_capability_rejected():
    with pytest.raises(HypothesisError):
        evaluate([BASELINE, BASELINE])

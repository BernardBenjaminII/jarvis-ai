import pytest

from core.bounty_agent.autonomy.hypothesis_ranker_r918d1 import (
    CAPABILITIES,
    RankingError,
    rank,
)


def baseline():
    return {
        "capability": "baseline_http",
        "state": "completed",
        "valid_product_response": True,
        "product_ids": [1, 2, 3],
    }


def syntax():
    return {
        "capability": "sql_syntax_diagnostic",
        "state": "completed",
        "http_status": 500,
        "sqlite_error": "SQLite error observed",
        "query_sha256": "a" * 64,
    }


def repeat():
    return {
        "capability": "syntax_repetition",
        "state": "completed",
        "http_status": 500,
        "sqlite_error": "SQLite error observed",
        "query_sha256": "a" * 64,
        "reproduces_syntax_error": True,
    }


def decide(items, budget=5, allowed=CAPABILITIES):
    return rank(
        observations=items,
        allowed_capabilities=allowed,
        remaining_budget=budget,
    )


def test_initial_baseline():
    assert decide([]).next_capability == "baseline_http"


def test_baseline_to_syntax():
    assert decide([baseline()]).next_capability == (
        "sql_syntax_diagnostic"
    )


def test_sql_signal_prioritizes_reproduction():
    result = decide([baseline(), syntax()])
    assert result.next_capability == "syntax_repetition"
    assert (
        "syntax_condition_reproduction_missing"
        in result.evidence_gaps
    )


def test_reproduced_sql_signal():
    result = decide([baseline(), syntax(), repeat()])
    assert result.hypotheses[0].identifier == (
        "sql_parser_interaction"
    )
    assert result.hypotheses[0].score == 80
    assert result.validated_vulnerability is False
    assert result.execution_allowed is False


def test_reproduction_unavailable():
    allowed = CAPABILITIES - {"syntax_repetition"}
    result = decide([baseline(), syntax()], allowed=allowed)
    assert result.next_capability == "boolean_comparison"


def test_budget_exhaustion():
    result = decide([baseline(), syntax()], budget=0)
    assert result.next_capability is None


def test_failed_attempt_stops():
    result = decide([{
        "capability": "baseline_http",
        "state": "failed",
    }])
    assert result.next_capability is None


def test_duplicate_rejected():
    with pytest.raises(RankingError):
        decide([baseline(), baseline()])


def test_invalid_budget_rejected():
    with pytest.raises(RankingError):
        decide([], budget=True)


def test_unknown_capability_rejected():
    with pytest.raises(RankingError):
        decide([{
            "capability": "external_scan",
            "state": "completed",
        }])


def test_contradictory_reproduction_rejected():
    bad = repeat()
    bad["reproduces_syntax_error"] = False

    with pytest.raises(RankingError):
        decide([baseline(), syntax(), bad])


def test_no_sql_signal_stops():
    normal = {
        "capability": "sql_syntax_diagnostic",
        "state": "completed",
        "http_status": 200,
        "sqlite_error": None,
    }
    result = decide([baseline(), normal])
    assert result.next_capability is None

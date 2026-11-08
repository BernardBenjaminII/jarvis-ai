"""Offline regression tests for R9.18E.1."""

import hashlib

import pytest

from core.bounty_agent.autonomy.adaptive_executor_r918 import CATALOG
from core.bounty_agent.autonomy.hypothesis_ranker_r918d1 import (
    CAPABILITIES,
    RankingError,
)
from core.bounty_agent.autonomy.investigation_planner_r918e1 import (
    EVIDENCE_VALUE,
    plan,
)


def observation(capability, **overrides):
    execution_capability = (
        "sql_syntax_diagnostic"
        if capability == "syntax_repetition"
        else capability
    )

    query = CATALOG[execution_capability][1]

    item = {
        "capability": capability,
        "state": "completed",
        "query_sha256": hashlib.sha256(
            query.encode("utf-8")
        ).hexdigest(),
        "http_status": 200,
        "valid_product_response": True,
        "sqlite_error": None,
    }

    if capability in {
        "sql_syntax_diagnostic",
        "syntax_repetition",
    }:
        item.update({
            "http_status": 500,
            "valid_product_response": False,
            "sqlite_error": "SQLite error observed",
        })

    if capability == "syntax_repetition":
        item["reproduces_syntax_error"] = True

    item.update(overrides)
    return item


def investigate(observations=None, budget=5, allowed=None):
    return plan(
        observations=(
            observations if observations is not None else []
        ),
        allowed_capabilities=(
            allowed if allowed is not None else CAPABILITIES
        ),
        remaining_budget=budget,
    )


def test_initial_baseline_recommended():
    result = investigate()
    assert result.next_capability == "baseline_http"
    assert "valid_baseline_missing" in result.evidence_gaps


def test_syntax_diagnostic_recommended_after_baseline():
    result = investigate([
        observation("baseline_http"),
    ])
    assert result.next_capability == "sql_syntax_diagnostic"


def test_syntax_repetition_recommended():
    result = investigate([
        observation("baseline_http"),
        observation("sql_syntax_diagnostic"),
    ])

    assert result.next_capability == "syntax_repetition"
    assert (
        "syntax_condition_reproduction_missing"
        in result.evidence_gaps
    )
    assert "exploitability_not_established" in result.evidence_gaps


def test_candidates_have_deterministic_utility():
    result = investigate([
        observation("baseline_http"),
        observation("sql_syntax_diagnostic"),
    ])

    assert result.candidates

    for candidate in result.candidates:
        assert candidate.information_value == (
            EVIDENCE_VALUE[candidate.capability]
        )
        assert candidate.relative_cost == 1
        assert candidate.utility == (
            candidate.information_value - 5
        )


def test_candidate_order_is_deterministic():
    history = [
        observation("baseline_http"),
        observation("sql_syntax_diagnostic"),
    ]

    first = investigate(history)
    second = investigate(history)

    assert first == second
    assert list(first.candidates) == sorted(
        first.candidates,
        key=lambda item: (-item.utility, item.capability),
    )


def test_reproduction_advances_recommendation():
    result = investigate([
        observation("baseline_http"),
        observation("sql_syntax_diagnostic"),
        observation("syntax_repetition"),
    ])

    assert result.next_capability == "boolean_comparison"
    assert "exploitability_not_established" in result.evidence_gaps


def test_exhausted_budget_stops():
    result = investigate(budget=0)

    assert result.next_capability is None
    assert result.stop_reason == "Request budget exhausted"


def test_no_sql_signal_stops():
    result = investigate([
        observation("baseline_http"),
        observation(
            "sql_syntax_diagnostic",
            http_status=200,
            sqlite_error=None,
            valid_product_response=True,
        ),
    ])

    assert result.next_capability is None
    assert result.stop_reason is not None


def test_failed_experiment_stops():
    result = investigate([
        observation(
            "baseline_http",
            state="failed",
        ),
    ])

    assert result.next_capability is None
    assert "human review" in result.stop_reason.lower()


def test_restricted_capabilities_respected():
    result = investigate(
        observations=[
            observation("baseline_http"),
            observation("sql_syntax_diagnostic"),
        ],
        allowed=frozenset({"boolean_comparison"}),
    )

    assert result.next_capability == "boolean_comparison"
    assert all(
        candidate.capability == "boolean_comparison"
        for candidate in result.candidates
    )


def test_empty_capability_set_stops():
    result = investigate(
        allowed=frozenset(),
    )
    assert result.next_capability is None


def test_invalid_budget_rejected():
    with pytest.raises(RankingError):
        investigate(budget=-1)


def test_unknown_capability_rejected():
    with pytest.raises(RankingError):
        investigate(
            allowed=frozenset({"unknown_capability"}),
        )


def test_duplicate_observation_rejected():
    with pytest.raises(RankingError):
        investigate([
            observation("baseline_http"),
            observation("baseline_http"),
        ])


def test_contradictory_reproduction_rejected():
    with pytest.raises(RankingError):
        investigate([
            observation("baseline_http"),
            observation("sql_syntax_diagnostic"),
            observation(
                "syntax_repetition",
                reproduces_syntax_error=False,
            ),
        ])


def test_planner_never_authorizes_execution():
    result = investigate()

    assert result.execution_allowed is False
    assert result.validated_vulnerability is False
    assert result.human_review_required is True
    assert result.submission_authorized is False


def test_completed_investigation_stops():
    result = investigate([
        observation("baseline_http"),
        observation("sql_syntax_diagnostic"),
        observation("syntax_repetition"),
        observation("boolean_comparison"),
        observation("reproducibility_check"),
    ], budget=0)

    assert result.next_capability is None
    assert result.candidates == ()
    assert result.validated_vulnerability is False
    assert result.human_review_required is True

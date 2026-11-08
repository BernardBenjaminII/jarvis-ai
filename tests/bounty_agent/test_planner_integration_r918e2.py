"""R9.18E.2: offline planner/controller integration tests."""

import hashlib
from dataclasses import replace

import pytest

import core.bounty_agent.autonomy.ranked_integration_r918d2 as integration
from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
    LocalMission,
)
from core.bounty_agent.autonomy.ranked_integration_r918d2 import (
    RankedIntegrationError,
    run_ranked,
)


def mission(budget=5, approved=True):
    return LocalMission(
        approved=approved,
        max_requests=budget,
    )


def fake_runner(capability):
    query = CATALOG[capability][1]
    result = {
        "capability": capability,
        "query_sha256": hashlib.sha256(
            query.encode("utf-8")
        ).hexdigest(),
        "http_status": 200,
        "valid_product_response": True,
        "product_ids": [1, 2, 3],
        "sqlite_error": None,
    }

    if capability == "sql_syntax_diagnostic":
        result.update({
            "http_status": 500,
            "valid_product_response": False,
            "product_ids": [],
            "sqlite_error": "SQLite error observed",
        })

    return result


def execute(*, budget=5, runner=fake_runner):
    return run_ranked(
        mission=mission(budget),
        runner=runner,
        ranked_mode=True,
        planner_mode=True,
    )


def test_planner_requires_ranked_mode():
    with pytest.raises(RankedIntegrationError):
        run_ranked(
            mission=mission(),
            runner=fake_runner,
            planner_mode=True,
        )


def test_invalid_planner_flag_rejected():
    with pytest.raises(RankedIntegrationError):
        run_ranked(
            mission=mission(),
            runner=fake_runner,
            ranked_mode=True,
            planner_mode="yes",
        )


def test_planner_execution_sequence():
    result = execute()
    assert [
        item["capability"]
        for item in result.observations
    ] == [
        "baseline_http",
        "sql_syntax_diagnostic",
        "syntax_repetition",
        "boolean_comparison",
        "reproducibility_check",
    ]
    assert result.request_count == 5


def test_planner_budget_enforced():
    result = execute(budget=2)
    assert result.request_count == 2


def test_planner_never_validates_vulnerability():
    result = execute()
    assert result.validated_vulnerability is False
    assert result.human_review_required is True
    assert result.submission_authorized is False


def test_unapproved_mission_rejected():
    with pytest.raises(Exception):
        run_ranked(
            mission=mission(approved=False),
            runner=fake_runner,
            ranked_mode=True,
            planner_mode=True,
        )


def test_executor_failure_stops():
    calls = []

    def failing_runner(capability):
        calls.append(capability)
        raise RuntimeError("Simulated failure")

    result = execute(runner=failing_runner)
    assert calls == ["baseline_http"]
    assert result.request_count == 1
    assert result.observations[0]["state"] == "failed"


def test_query_integrity_failure_stops():
    def bad_runner(capability):
        result = fake_runner(capability)
        result["query_sha256"] = "0" * 64
        return result

    result = execute(runner=bad_runner)
    assert result.request_count == 1
    assert result.observations[0]["failure_category"] == (
        "evidence_integrity_failure"
    )


def test_planner_exception_fails_closed(monkeypatch):
    def broken_plan(**kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(integration, "plan", broken_plan)

    calls = []
    result = execute(
        runner=lambda capability: calls.append(capability)
    )

    assert calls == []
    assert result.request_count == 0
    assert result.stop_reason == "planner_failure"


def test_planner_cannot_authorize_execution(monkeypatch):
    original = integration.plan

    def unsafe_plan(**kwargs):
        return replace(
            original(**kwargs),
            execution_allowed=True,
        )

    monkeypatch.setattr(integration, "plan", unsafe_plan)

    calls = []
    result = execute(
        runner=lambda capability: calls.append(capability)
    )

    assert calls == []
    assert result.request_count == 0
    assert result.stop_reason == "invalid_planner_safety_flags"


def test_invalid_recommendation_stops(monkeypatch):
    original = integration.plan

    def invalid_plan(**kwargs):
        return replace(
            original(**kwargs),
            next_capability="unapproved_experiment",
        )

    monkeypatch.setattr(integration, "plan", invalid_plan)

    calls = []
    result = execute(
        runner=lambda capability: calls.append(capability)
    )

    assert calls == []
    assert result.request_count == 0
    assert result.stop_reason == "invalid_planner_recommendation"


def test_no_sql_signal_stops_early():
    def normal_runner(capability):
        result = fake_runner(capability)
        if capability == "sql_syntax_diagnostic":
            result.update({
                "http_status": 200,
                "valid_product_response": True,
                "sqlite_error": None,
            })
        return result

    result = execute(runner=normal_runner)
    assert result.request_count == 2
    assert result.validated_vulnerability is False


def test_default_legacy_mode_preserved():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
    )
    assert result.request_count == 5


def test_existing_ranked_mode_preserved():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
        ranked_mode=True,
    )
    assert result.request_count == 5

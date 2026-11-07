import hashlib

import pytest

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
    LocalMission,
)
from core.bounty_agent.autonomy.ranked_integration_r918d2 import (
    RankedIntegrationError,
    run_ranked,
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


def mission(budget=5):
    return LocalMission(
        approved=True,
        max_requests=budget,
    )


def test_legacy_mode_unchanged():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
    )
    assert result.request_count == 5
    assert result.observations[2]["capability"] == (
        "syntax_repetition"
    )


def test_ranked_execution_sequence():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
        ranked_mode=True,
    )

    names = [
        item["capability"]
        for item in result.observations
    ]

    assert names == [
        "baseline_http",
        "sql_syntax_diagnostic",
        "syntax_repetition",
        "boolean_comparison",
        "reproducibility_check",
    ]


def test_reproduced_diagnostic():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
        ranked_mode=True,
    )
    assert (
        result.observations[2]["reproduces_syntax_error"]
        is True
    )


def test_budget_enforced():
    result = run_ranked(
        mission=mission(2),
        runner=fake_runner,
        ranked_mode=True,
    )
    assert result.request_count == 2


def test_no_automatic_validation():
    result = run_ranked(
        mission=mission(),
        runner=fake_runner,
        ranked_mode=True,
    )
    assert result.validated_vulnerability is False
    assert result.submission_authorized is False
    assert result.human_review_required is True


def test_unapproved_mission_rejected():
    with pytest.raises(Exception):
        run_ranked(
            mission=LocalMission(approved=False),
            runner=fake_runner,
            ranked_mode=True,
        )


def test_invalid_mode_rejected():
    with pytest.raises(RankedIntegrationError):
        run_ranked(
            mission=mission(),
            runner=fake_runner,
            ranked_mode="yes",
        )


def test_executor_failure_stops():
    def failing_runner(capability):
        raise RuntimeError("Simulated failure")

    result = run_ranked(
        mission=mission(),
        runner=failing_runner,
        ranked_mode=True,
    )

    assert result.request_count == 1
    assert result.observations[0]["state"] == "failed"
    assert result.stop_reason == (
        "execution_or_evidence_failure"
    )


def test_query_integrity_failure_stops():
    def bad_runner(capability):
        result = fake_runner(capability)
        result["query_sha256"] = "0" * 64
        return result

    result = run_ranked(
        mission=mission(),
        runner=bad_runner,
        ranked_mode=True,
    )

    assert result.request_count == 1
    assert result.observations[0]["failure_category"] == (
        "evidence_integrity_failure"
    )


def test_no_sql_signal_stops_early():
    def normal_runner(capability):
        result = fake_runner(capability)
        if capability == "sql_syntax_diagnostic":
            result.update({
                "http_status": 200,
                "sqlite_error": None,
                "valid_product_response": True,
            })
        return result

    result = run_ranked(
        mission=mission(),
        runner=normal_runner,
        ranked_mode=True,
    )

    assert result.request_count == 2
    assert result.validated_vulnerability is False

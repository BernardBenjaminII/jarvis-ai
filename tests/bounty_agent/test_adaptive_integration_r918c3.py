import hashlib

import pytest

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
    LocalMission,
)
from core.bounty_agent.autonomy.adaptive_integration_r918c3 import (
    run_integrated,
)


def fake_runner(capability):
    query = CATALOG[capability][1]

    result = {
        "capability": capability,
        "query_sha256": hashlib.sha256(
            query.encode()
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


def test_syntax_condition_is_repeated():
    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=fake_runner,
    )

    names = [
        item["capability"]
        for item in result.observations
    ]

    assert names[:3] == [
        "baseline_http",
        "sql_syntax_diagnostic",
        "syntax_repetition",
    ]

    original = result.observations[1]
    repeated = result.observations[2]

    assert (
        original["query_sha256"]
        == repeated["query_sha256"]
    )
    assert repeated["reproduces_syntax_error"] is True
    assert result.validated_vulnerability is False
    assert result.submission_authorized is False
    assert result.request_count <= 5


def test_unapproved_mission_rejected():
    with pytest.raises(Exception):
        run_integrated(
            mission=LocalMission(approved=False),
            runner=fake_runner,
        )


def test_budget_boundary():
    result = run_integrated(
        mission=LocalMission(
            approved=True,
            max_requests=2,
        ),
        runner=fake_runner,
    )

    assert result.request_count == 2
    assert all(
        item["capability"] != "syntax_repetition"
        for item in result.observations
    )


def test_executor_failure_stops():
    def failing_runner(capability):
        raise RuntimeError("Simulated failure")

    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=failing_runner,
    )

    assert result.request_count == 1
    assert result.observations[0]["state"] == "failed"
    assert result.validated_vulnerability is False


def test_query_hash_mismatch_stops():
    calls = 0

    def mismatched_runner(capability):
        nonlocal calls
        calls += 1
        result = fake_runner(capability)

        if calls == 3:
            result["query_sha256"] = "0" * 64

        return result

    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=mismatched_runner,
    )

    assert result.stop_reason == "execution_or_evidence_failure"
    assert result.observations[2]["state"] == "failed"


def test_request_budget_never_exceeded():
    result = run_integrated(
        mission=LocalMission(
            approved=True,
            max_requests=5,
        ),
        runner=fake_runner,
    )
    assert result.request_count <= 5
    assert result.human_review_required is True


def test_canonical_query_hash_required():
    def incorrect_runner(capability):
        result = fake_runner(capability)
        result["query_sha256"] = "a" * 64
        return result

    result = run_integrated(
        mission=LocalMission(approved=True),
        runner=incorrect_runner,
    )

    assert result.request_count == 1
    assert result.observations[0]["state"] == "failed"
    assert result.stop_reason == "execution_or_evidence_failure"
    assert result.validated_vulnerability is False

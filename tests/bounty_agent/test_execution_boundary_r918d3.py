import hashlib

import pytest

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
)
from core.bounty_agent.autonomy.execution_boundary_r918d3 import (
    BoundaryError,
    execute_verified,
)


def runner(capability):
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


def execute(capability, observations=None, custom_runner=None):
    return execute_verified(
        capability=capability,
        runner=custom_runner or runner,
        observations=observations if observations is not None else [],
        rationale="Test experiment",
    )


def test_baseline_execution():
    entry = execute("baseline_http")
    assert entry["state"] == "completed"
    assert entry["valid_product_response"] is True


def test_syntax_execution():
    entry = execute("sql_syntax_diagnostic")
    assert entry["state"] == "completed"
    assert entry["http_status"] == 500


def test_syntax_repetition():
    original = execute("sql_syntax_diagnostic")
    repeated = execute("syntax_repetition", [original])
    assert repeated["state"] == "completed"
    assert repeated["reproduces_syntax_error"] is True
    assert repeated["query_sha256"] == original["query_sha256"]


def test_unapproved_experiment_rejected():
    with pytest.raises(BoundaryError):
        execute("arbitrary_experiment")


def test_duplicate_experiment_rejected():
    original = execute("baseline_http")
    with pytest.raises(BoundaryError):
        execute("baseline_http", [original])


def test_repetition_without_diagnostic_rejected():
    with pytest.raises(BoundaryError):
        execute("syntax_repetition")


def test_query_hash_mismatch():
    def incorrect(capability):
        result = runner(capability)
        result["query_sha256"] = "0" * 64
        return result

    entry = execute(
        "baseline_http",
        custom_runner=incorrect,
    )
    assert entry["state"] == "failed"
    assert entry["failure_category"] == (
        "evidence_integrity_failure"
    )


def test_capability_mismatch():
    def incorrect(capability):
        result = runner(capability)
        result["capability"] = "other"
        return result

    entry = execute(
        "baseline_http",
        custom_runner=incorrect,
    )
    assert entry["state"] == "failed"


def test_executor_failure():
    def failing(capability):
        raise RuntimeError("Simulated failure")

    entry = execute(
        "baseline_http",
        custom_runner=failing,
    )
    assert entry["state"] == "failed"
    assert entry["failure_category"] == "executor_failure"


def test_invalid_executor_response():
    entry = execute(
        "baseline_http",
        custom_runner=lambda capability: None,
    )
    assert entry["state"] == "failed"
    assert entry["failure_category"] == (
        "evidence_integrity_failure"
    )


def test_repetition_requires_valid_syntax_signal():
    original = execute("sql_syntax_diagnostic")
    original["sqlite_error"] = None

    with pytest.raises(BoundaryError):
        execute("syntax_repetition", [original])

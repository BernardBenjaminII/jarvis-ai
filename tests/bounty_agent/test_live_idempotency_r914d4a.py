from concurrent.futures import ThreadPoolExecutor

import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore


@pytest.fixture
def environment(tmp_path):
    auths = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="synthetic reviewed rules",
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    return auths, auth, live


def test_first_correlated_creation(environment):
    _, auth, live = environment

    mid = live.create(
        auth, budget=5, operation_id="op-1"
    )

    report = live.report(mid)

    assert report["mission"]["operation_id"] == "op-1"


def test_repeated_operation_returns_same_mission(environment):
    _, auth, live = environment

    first = live.create(
        auth, budget=5, operation_id="op-1"
    )
    second = live.create(
        auth, budget=5, operation_id="op-1"
    )

    assert first == second

    with live.db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM missions"
        ).fetchone()[0]

    assert count == 1


def test_budget_mismatch_rejected(environment):
    _, auth, live = environment

    live.create(auth, budget=5, operation_id="op-1")

    with pytest.raises(ValueError):
        live.create(
            auth, budget=10, operation_id="op-1"
        )


def test_authorization_mismatch_rejected(environment):
    auths, auth, live = environment

    second_auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="different synthetic review",
        ttl=3600,
    )

    live.create(auth, budget=5, operation_id="op-1")

    with pytest.raises(ValueError):
        live.create(
            second_auth,
            budget=5,
            operation_id="op-1",
        )


def test_concurrent_creation_is_idempotent(environment):
    _, auth, live = environment

    def create(_):
        return live.create(
            auth,
            budget=5,
            operation_id="op-concurrent",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(create, range(16)))

    assert len(set(results)) == 1


def test_legacy_calls_create_distinct_missions(environment):
    _, auth, live = environment

    first = live.create(auth, budget=5)
    second = live.create(auth, budget=5)

    assert first != second


def test_invalid_operation_id_rejected(environment):
    _, auth, live = environment

    with pytest.raises(ValueError):
        live.create(
            auth, budget=5, operation_id=""
        )


def test_reopen_store_reuses_mission(environment):
    auths, auth, live = environment

    first = live.create(
        auth, budget=5, operation_id="op-restart"
    )

    reopened = LiveMissionStore(
        live.path,
        authorization_store=auths,
    )

    second = reopened.create(
        auth, budget=5, operation_id="op-restart"
    )

    assert first == second

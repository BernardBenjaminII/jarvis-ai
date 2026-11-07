from concurrent.futures import ThreadPoolExecutor

import pytest

from core.bounty_agent.autonomy.scheduler import MissionClaimStore


@pytest.fixture
def claimed(tmp_path):
    store = MissionClaimStore(tmp_path / "scheduler.sqlite")
    result = store.claim(
        authorization="auth-test",
        program="training",
        target="training.example",
        policy_digest="policy-v1",
    )
    return store, result["claim"]["claim_key"]


def test_first_completion(claimed):
    store, key = claimed

    assert store.mark_created(key, "session-1", "mission-1") is True
    assert store.get(key)["state"] == "created"


def test_identical_retry(claimed):
    store, key = claimed

    store.mark_created(key, "session-1", "mission-1")

    assert store.mark_created(
        key, "session-1", "mission-1"
    ) is False


def test_different_session_rejected(claimed):
    store, key = claimed

    store.mark_created(key, "session-1", "mission-1")

    with pytest.raises(ValueError):
        store.mark_created(key, "session-2", "mission-1")


def test_different_mission_rejected(claimed):
    store, key = claimed

    store.mark_created(key, "session-1", "mission-1")

    with pytest.raises(ValueError):
        store.mark_created(key, "session-1", "mission-2")


def test_concurrent_identical_completion(claimed):
    store, key = claimed

    def complete(_):
        return store.mark_created(
            key, "session-1", "mission-1"
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(complete, range(16)))

    assert results.count(True) == 1
    assert results.count(False) == 15


def test_single_created_event(claimed):
    store, key = claimed

    for _ in range(5):
        store.mark_created(key, "session-1", "mission-1")

    with store.connect() as db:
        count = db.execute(
            """
            SELECT COUNT(*) FROM claim_events
            WHERE claim_key=? AND kind='created'
            """,
            (key,),
        ).fetchone()[0]

    assert count == 1


def test_missing_claim_rejected(claimed):
    store, _ = claimed

    with pytest.raises(ValueError, match="Unknown claim"):
        store.mark_created(
            "nonexistent", "session-1", "mission-1"
        )


def test_completion_survives_restart(claimed):
    store, key = claimed

    store.mark_created(key, "session-1", "mission-1")

    reopened = MissionClaimStore(store.path)

    assert reopened.mark_created(
        key, "session-1", "mission-1"
    ) is False

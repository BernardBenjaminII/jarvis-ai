from concurrent.futures import ThreadPoolExecutor

import pytest

from core.bounty_agent.autonomy.scheduler import (
    MissionClaimStore,
)


@pytest.fixture
def store(tmp_path):
    return MissionClaimStore(
        tmp_path / "scheduler.sqlite"
    )


def request():
    return {
        "authorization": "auth-test",
        "program": "training",
        "target": "training.example",
        "policy_digest": "synthetic-policy-v1",
    }


def test_first_claim_acquired(store):
    result = store.claim(**request())

    assert result["acquired"] is True
    assert result["claim"]["state"] == "claimed"


def test_duplicate_claim_rejected(store):
    first = store.claim(**request())
    second = store.claim(**request())

    assert first["acquired"] is True
    assert second["acquired"] is False

    assert (
        first["claim"]["claim_key"]
        == second["claim"]["claim_key"]
    )


def test_claim_survives_restart(store):
    first = store.claim(**request())

    reopened = MissionClaimStore(store.path)
    second = reopened.claim(**request())

    assert first["acquired"] is True
    assert second["acquired"] is False
    assert len(reopened.pending()) == 1


def test_concurrent_claims_have_one_winner(store):
    def acquire(_):
        return store.claim(**request())["acquired"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(acquire, range(16)))

    assert sum(results) == 1


def test_created_claim_is_persistent(store):
    first = store.claim(**request())
    key = first["claim"]["claim_key"]

    store.mark_created(
        key,
        session_id="session-test",
        mission_id="mission-test",
    )

    reopened = MissionClaimStore(store.path)
    record = reopened.get(key)

    assert record["state"] == "created"
    assert record["session_id"] == "session-test"
    assert record["mission_id"] == "mission-test"
    assert reopened.pending() == []


def test_created_claim_cannot_be_overwritten(store):
    key = store.claim(**request())["claim"]["claim_key"]

    store.mark_created(key, "session-1", "mission-1")

    with pytest.raises(ValueError):
        store.mark_created(
            key, "session-2", "mission-2"
        )

    assert store.get(key)["session_id"] == "session-1"


def test_different_targets_have_different_claims(store):
    first = store.claim(**request())

    other = request()
    other["target"] = "other.example"

    second = store.claim(**other)

    assert first["acquired"] is True
    assert second["acquired"] is True


def test_invalid_claim_rejected(store):
    invalid = request()
    invalid["authorization"] = ""

    with pytest.raises(ValueError):
        store.claim(**invalid)

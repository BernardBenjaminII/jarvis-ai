import sqlite3
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


def request(policy="policy-v1"):
    return {
        "authorization": "auth-test",
        "program": "training",
        "target": "training.example",
        "policy_digest": policy,
    }


def test_first_policy_claim_acquired(store):
    result = store.claim(**request())
    assert result["acquired"] is True


def test_different_policy_cannot_duplicate_active_claim(store):
    store.claim(**request("policy-v1"))

    with pytest.raises(sqlite3.IntegrityError):
        store.claim(**request("policy-v2"))

    with store.connect() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM claims"
        ).fetchone()[0]

    assert count == 1


def test_created_claim_still_blocks_new_policy(store):
    first = store.claim(**request("policy-v1"))
    key = first["claim"]["claim_key"]

    store.mark_created(key, "session-1", "mission-1")

    with pytest.raises(sqlite3.IntegrityError):
        store.claim(**request("policy-v2"))


def test_different_targets_remain_independent(store):
    first = store.claim(**request())

    other = request()
    other["target"] = "other.example"

    second = store.claim(**other)

    assert first["acquired"] is True
    assert second["acquired"] is True


def test_concurrent_different_policy_claims(store):
    def acquire(index):
        try:
            return store.claim(
                **request(f"policy-v{index}")
            )["acquired"]
        except sqlite3.IntegrityError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(acquire, range(16)))

    assert sum(results) == 1


def test_migration_rejects_existing_conflicts(tmp_path):
    path = tmp_path / "legacy.sqlite"

    original = MissionClaimStore(path)
    original.claim(**request("policy-v1"))

    with sqlite3.connect(path) as db:
        db.execute(
            "DROP INDEX active_claim_target_unique"
        )

    # Simulate a conflicting record written by an older
    # scheduler version, bypassing current claim() validation.
    legacy = request("policy-v2")
    legacy_key = original.key(
        legacy["authorization"],
        legacy["program"],
        legacy["target"],
        legacy["policy_digest"],
    )

    with sqlite3.connect(path) as db:
        db.execute(
            """
            INSERT INTO claims(
                claim_key, authorization, program,
                target, policy_digest, state,
                created, updated
            ) VALUES(?,?,?,?,?,'claimed',?,?)
            """,
            (
                legacy_key,
                legacy["authorization"],
                legacy["program"],
                legacy["target"],
                legacy["policy_digest"],
                100.0,
                100.0,
            ),
        )

    with pytest.raises(
        ValueError,
        match="Conflicting active scheduler claims",
    ):
        MissionClaimStore(path)

    # Migration must not destroy existing records.
    with sqlite3.connect(path) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM claims"
        ).fetchone()[0]

    assert count == 2

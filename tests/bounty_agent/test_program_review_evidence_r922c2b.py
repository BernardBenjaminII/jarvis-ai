"""R9.22C2B: stored-review evidence regression."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from core.capabilities.kali_workstation import TOOLS
from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_reviews_r921e3 import (
    ScopeReviewStore,
)
from core.bounty_agent.autonomy.program_review_evidence_r922c2b import (
    assess_persistent_review,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)


def draft(restrictions=None):
    return create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["admin.training.example"],
        restrictions=restrictions or ["No automated scanning"],
    )


def inventory():
    return {
        "state": "ready",
        "mode": "inventory_only",
        "execution_authorized": False,
        "tool_count": len(TOOLS),
        "installed_count": len(TOOLS),
        "tools": {
            name: {
                "installed": True,
                "path": f"/usr/bin/{name}",
            }
            for name in TOOLS
        },
    }


def attest(tmp_path, policy=None):
    policy = policy or draft()
    store = ScopeReviewStore(tmp_path / "reviews.sqlite3")

    result = store.attest(
        draft_id="training-draft",
        draft=policy,
        reviewer="synthetic-test-operator",
        source_checked_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source_matches=True,
    )

    return store, result["id"], policy


def evaluate(policy=None, **kwargs):
    return assess_persistent_review(
        draft_id="training-draft",
        draft=policy or draft(),
        inventory=inventory(),
        **kwargs,
    )


def test_without_attestation_remains_unverified():
    result = evaluate()

    assert result["attestation"]["state"] == "not_attested"
    assert result["attestation"][
        "stored_operator_attestation_valid"
    ] is False
    assert result["execution_enabled"] is False


def test_current_stored_attestation(tmp_path):
    store, review_id, policy = attest(tmp_path)

    result = evaluate(
        policy,
        review_store=store,
        review_id=review_id,
        restriction_evidence={
            "template_analysis": "No automated scanning",
        },
    )

    assert result["attestation"]["state"] == (
        "operator_attested_current"
    )
    assert result["attestation"][
        "policy_digest_matched"
    ] is True
    assert result["attestation"][
        "independently_verified"
    ] is False
    assert result["attestation"][
        "category_classifications_persisted"
    ] is False
    assert result["testing_authorized"] is False
    assert result["mission_creation_allowed"] is False


def test_wrong_draft_identity_rejected(tmp_path):
    store, review_id, policy = attest(tmp_path)

    result = assess_persistent_review(
        draft_id="different-draft",
        draft=policy,
        inventory=inventory(),
        review_store=store,
        review_id=review_id,
    )

    assert result["attestation"]["state"] == (
        "invalid_or_expired"
    )


def test_changed_policy_digest_rejected(tmp_path):
    store, review_id, _ = attest(tmp_path)

    changed = draft([
        "No automated scanning",
        "No credential attacks",
    ])

    result = evaluate(
        changed,
        review_store=store,
        review_id=review_id,
    )

    assert result["attestation"]["state"] == (
        "invalid_or_expired"
    )


def test_expired_review_rejected(tmp_path):
    store, review_id, policy = attest(tmp_path)

    with store.db() as db:
        row = db.execute(
            "SELECT review_json FROM scope_reviews WHERE id = ?",
            (review_id,),
        ).fetchone()

        review = json.loads(row["review_json"])
        review["expires_at"] = (
            datetime.now(timezone.utc)
            - timedelta(seconds=10)
        ).isoformat()

        db.execute(
            "UPDATE scope_reviews SET review_json = ? WHERE id = ?",
            (json.dumps(review), review_id),
        )

    result = evaluate(
        policy,
        review_store=store,
        review_id=review_id,
    )

    assert result["attestation"]["state"] == (
        "invalid_or_expired"
    )


def test_nonexistent_review_rejected(tmp_path):
    store, _, policy = attest(tmp_path)

    result = evaluate(
        policy,
        review_store=store,
        review_id="nonexistent-review",
    )

    assert result["attestation"]["state"] == (
        "invalid_or_expired"
    )


def test_missing_store_fails_closed():
    with pytest.raises(OpportunityQueueError):
        evaluate(review_id="some-review")


def test_unrecorded_restriction_rejected():
    with pytest.raises(OpportunityQueueError):
        evaluate(
            restriction_evidence={
                "http_observation": "All scanning permitted"
            }
        )

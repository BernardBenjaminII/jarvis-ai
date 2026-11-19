"""R9.21E3 review persistence and authorization separation."""

from datetime import datetime, timedelta, timezone

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_reviews_r921e3 import (
    ScopeReviewStore,
    ScopeReviewStoreError,
)


@pytest.fixture
def draft():
    return create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["admin.training.example"],
        restrictions=["No automated scanning"],
    )


def attest(store, draft):
    checked = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()

    return store.attest(
        draft_id="draft-123",
        draft=draft,
        reviewer="human-reviewer",
        source_checked_at=checked,
        source_matches=True,
    )


def test_persist_and_retrieve(tmp_path, draft):
    path = tmp_path / "reviews.sqlite"
    store = ScopeReviewStore(path)

    saved = attest(store, draft)

    reloaded = ScopeReviewStore(path)
    record = reloaded.get(
        saved["id"],
        draft_id="draft-123",
        draft=draft,
    )

    assert record["review"]["review_status"] == "operator_attested"
    assert record["execution_authorized"] is False
    assert record["submission_authorized"] is False


def test_unverified_source_not_attestable(tmp_path, draft):
    store = ScopeReviewStore(tmp_path / "reviews.sqlite")

    with pytest.raises(ValueError):
        store.attest(
            draft_id="draft-123",
            draft=draft,
            reviewer="human-reviewer",
            source_checked_at=datetime.now(
                timezone.utc
            ).isoformat(),
            source_matches=False,
        )


def test_wrong_draft_id_rejected(tmp_path, draft):
    store = ScopeReviewStore(tmp_path / "reviews.sqlite")
    saved = attest(store, draft)

    with pytest.raises(ScopeReviewStoreError):
        store.get(
            saved["id"],
            draft_id="different-draft",
            draft=draft,
        )


def test_modified_policy_rejected(tmp_path, draft):
    store = ScopeReviewStore(tmp_path / "reviews.sqlite")
    saved = attest(store, draft)

    modified = dict(draft)
    modified["program"] = "Different Program"

    with pytest.raises(ValueError):
        store.get(
            saved["id"],
            draft_id="draft-123",
            draft=modified,
        )


def test_expired_review_rejected(tmp_path, draft):
    store = ScopeReviewStore(tmp_path / "reviews.sqlite")
    saved = attest(store, draft)

    with store.db() as db:
        row = db.execute(
            "SELECT review_json FROM scope_reviews WHERE id = ?",
            (saved["id"],),
        ).fetchone()

        import json
        review = json.loads(row["review_json"])
        review["expires_at"] = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        ).isoformat()

        db.execute(
            "UPDATE scope_reviews SET review_json = ? WHERE id = ?",
            (json.dumps(review), saved["id"]),
        )

    with pytest.raises(ScopeReviewStoreError):
        store.get(
            saved["id"],
            draft_id="draft-123",
            draft=draft,
        )


def test_database_file_private(tmp_path):
    path = tmp_path / "reviews.sqlite"
    ScopeReviewStore(path)

    assert path.stat().st_mode & 0o077 == 0

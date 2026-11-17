import json
import sqlite3

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
    ProgramScopeStoreError,
)


@pytest.fixture
def store(tmp_path):
    return ProgramScopeStore(tmp_path / "scope.db")


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


def test_import_and_retrieve(store, draft):
    identity = store.import_draft(draft)
    result = store.get_draft(identity)

    assert result["draft"]["policy_sha256"] == (
        draft["policy_sha256"]
    )
    assert result["review_status"] == "unverified"
    assert result["execution_authorized"] is False


def test_duplicate_import_idempotent(store, draft):
    first = store.import_draft(draft)
    second = store.import_draft(draft)

    assert first == second
    assert len(store.list_drafts()) == 1


def test_persists_across_instances(tmp_path, draft):
    path = tmp_path / "persistent.db"

    first = ProgramScopeStore(path)
    identity = first.import_draft(draft)

    second = ProgramScopeStore(path)

    assert second.get_draft(identity)["draft"][
        "policy_sha256"
    ] == draft["policy_sha256"]


def test_import_does_not_approve(store, draft):
    identity = store.import_draft(draft)
    result = store.get_draft(identity)

    assert result["execution_authorized"] is False
    assert result["submission_authorized"] is False
    assert result["draft"]["scope_verified"] is False


def test_unknown_draft_rejected(store):
    with pytest.raises(ProgramScopeStoreError):
        store.get_draft("missing")


def test_modified_content_rejected(store, draft):
    identity = store.import_draft(draft)

    with sqlite3.connect(store.path) as db:
        row = db.execute(
            "SELECT content_json FROM scope_drafts WHERE id=?",
            (identity,),
        ).fetchone()

        changed = json.loads(row[0])
        changed["in_scope"].append(
            "admin2.training.example"
        )

        db.execute(
            "UPDATE scope_drafts SET content_json=? WHERE id=?",
            (json.dumps(changed), identity),
        )

    with pytest.raises(ProgramScopeStoreError):
        store.get_draft(identity)


def test_list_only_unverified_metadata(store, draft):
    store.import_draft(draft)
    records = store.list_drafts()

    assert len(records) == 1
    assert records[0]["review_status"] == "unverified"
    assert records[0]["execution_authorized"] is False


def test_import_event_written(store, draft):
    identity = store.import_draft(draft)

    with store.db() as db:
        events = db.execute(
            "SELECT event_type FROM scope_events WHERE draft_id=?",
            (identity,),
        ).fetchall()

    assert [row["event_type"] for row in events] == [
        "draft_imported"
    ]


def test_reject_invalid_list_limit(store):
    with pytest.raises(ProgramScopeStoreError):
        store.list_drafts(0)

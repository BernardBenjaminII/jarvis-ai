"""R9.21E2: real authorization-store integration tests."""

from datetime import datetime, timezone, timedelta

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    review_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_bridge_r921e import (
    assess_authorization_binding,
)
from core.bounty_authorization.store import AuthorizationStore


def fixture_data(tmp_path):
    draft = create_scope_draft(
        platform="hackerone",
        program="Synthetic Training",
        policy_url="https://hackerone.com/training",
        in_scope=["api.training.example"],
        out_of_scope=["admin.training.example"],
        restrictions=["No automated scanning"],
    )

    now = datetime.now(timezone.utc)

    review = review_scope_draft(
        draft,
        reviewer="test-reviewer",
        source_checked_at=(
            now - timedelta(minutes=1)
        ).isoformat(),
        source_matches=True,
    )

    store = AuthorizationStore(tmp_path / "authorization.sqlite")

    return draft, review, store


def authorize(store, *, program="Synthetic Training"):
    return store.create(
        program=program,
        include=["api.training.example"],
        exclude=["admin.training.example"],
        capabilities=["subfinder"],
        reviewer="independent-reviewer",
        source_material="Synthetic reviewed authorization",
        ttl=3600,
    )


def assess(draft, review, store, auth_id, host="api.training.example"):
    return assess_authorization_binding(
        draft=draft,
        review=review,
        hostname=host,
        authorization_id=auth_id,
        authorization_store=store,
    )


def test_real_authorization_match(tmp_path):
    draft, review, store = fixture_data(tmp_path)
    auth_id = authorize(store)

    result = assess(draft, review, store, auth_id)

    assert result["authorization_match"] is True
    assert result["proposal_ready"] is False
    assert result["execution_started"] is False


def test_real_revocation_fails_closed(tmp_path):
    draft, review, store = fixture_data(tmp_path)
    auth_id = authorize(store)

    store.revoke(auth_id, "integration test")

    result = assess(draft, review, store, auth_id)

    assert result["authorization_match"] is False
    assert result["execution_started"] is False


def test_real_program_mismatch_fails_closed(tmp_path):
    draft, review, store = fixture_data(tmp_path)
    auth_id = authorize(store, program="Other Program")

    result = assess(draft, review, store, auth_id)

    assert result["authorization_match"] is False


def test_real_unknown_authorization_fails_closed(tmp_path):
    draft, review, store = fixture_data(tmp_path)

    result = assess(
        draft, review, store, "nonexistent-authorization"
    )

    assert result["authorization_match"] is False


def test_real_expired_authorization_fails_closed(tmp_path):
    draft, review, store = fixture_data(tmp_path)
    auth_id = authorize(store)

    # Modify only the temporary test database.
    with store.db() as db:
        db.execute(
            "UPDATE authorizations SET expires = ? WHERE id = ?",
            (0, auth_id),
        )

    result = assess(draft, review, store, auth_id)

    assert result["authorization_match"] is False


def test_real_host_exclusion_fails_closed(tmp_path):
    draft, review, store = fixture_data(tmp_path)
    auth_id = authorize(store)

    result = assess(
        draft,
        review,
        store,
        auth_id,
        "admin.training.example",
    )

    assert result["authorization_match"] is False

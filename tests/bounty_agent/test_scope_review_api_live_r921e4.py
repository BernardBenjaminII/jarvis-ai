"""R9.21E4 live SQLite authorization API integration."""

import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.bounty_authorization.store import AuthorizationStore
from core.src.routes.program_scopes_r921d import router
from core.src.routes import program_scope_reviews_r921e4 as review_api


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-reviewer")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "test-password-" + "x" * 40,
    )

    store = AuthorizationStore(tmp_path / "test_auth.sqlite")
    monkeypatch.setattr(
        review_api, "AuthorizationStore", lambda: store
    )

    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/bounty-agent",
        dependencies=[Depends(require_bounty_access)],
    )

    client = TestClient(app)

    credentials = base64.b64encode(
        ("test-reviewer:test-password-" + "x" * 40).encode()
    ).decode()

    headers = {"Authorization": "Basic " + credentials}

    draft = client.post(
        "/api/bounty-agent/program-scopes",
        headers=headers,
        json={
            "platform": "hackerone",
            "program": "Synthetic Training",
            "policy_url": "https://hackerone.com/training",
            "in_scope": ["api.training.example"],
            "out_of_scope": ["admin.training.example"],
            "restrictions": ["No automated scanning"],
        },
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    review = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        headers=headers,
        json={
            "source_checked_at": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ).isoformat(),
            "source_matches": True,
        },
    )
    assert review.status_code == 201

    auth_id = store.create(
        program="Synthetic Training",
        include=["api.training.example"],
        exclude=["admin.training.example"],
        capabilities=["subfinder"],
        reviewer="independent-reviewer",
        source_material="Synthetic test authorization",
        ttl=3600,
    )

    def assess(host="api.training.example"):
        return client.post(
            f"/api/bounty-agent/program-scopes/{draft_id}"
            "/authorization-assessment",
            headers=headers,
            json={
                "review_id": review.json()["id"],
                "hostname": host,
                "authorization_id": auth_id,
            },
        )

    return store, auth_id, assess


def test_active_matching_authorization(setup):
    _, _, assess = setup

    response = assess()
    assert response.status_code == 200
    result = response.json()

    assert result["authorization_match"] is True
    assert result["proposal_ready"] is False
    assert result["execution_started"] is False
    assert result["execution_authorized"] is False


def test_revoked_authorization_denied(setup):
    store, auth_id, assess = setup

    store.revoke(auth_id, "integration test")

    result = assess().json()

    assert result["authorization_match"] is False
    assert result["execution_started"] is False


def test_expired_authorization_denied(setup):
    store, auth_id, assess = setup

    with store.db() as db:
        db.execute(
            "UPDATE authorizations SET expires=0 WHERE id=?",
            (auth_id,),
        )

    result = assess().json()

    assert result["authorization_match"] is False
    assert result["execution_started"] is False


def test_excluded_target_denied(setup):
    _, _, assess = setup

    result = assess("admin.training.example").json()

    assert result["authorization_match"] is False
    assert result["execution_started"] is False

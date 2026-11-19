"""R9.21E4 authenticated review API regression."""

import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.src.routes.program_scopes_r921d import router


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv(
        "JARVIS_RUNTIME_ROOT",
        str(tmp_path / "runtime"),
    )
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "reviewer-test")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "synthetic-password-" + "x" * 40,
    )

    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/bounty-agent",
        dependencies=[Depends(require_bounty_access)],
    )

    return TestClient(app)


def auth():
    raw = ("reviewer-test:synthetic-password-" + "x" * 40)
    return {
        "Authorization": "Basic "
        + base64.b64encode(raw.encode()).decode()
    }


def policy():
    return {
        "platform": "hackerone",
        "program": "Synthetic Training",
        "policy_url": "https://hackerone.com/training",
        "in_scope": ["api.training.example"],
        "out_of_scope": ["admin.training.example"],
        "restrictions": ["No automated scanning"],
    }


def make_draft(client):
    response = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
        headers=auth(),
    )
    assert response.status_code == 201
    return response.json()["id"]


def review_request():
    return {
        "source_checked_at": (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        ).isoformat(),
        "source_matches": True,
    }


def test_review_requires_authentication(client):
    draft_id = make_draft(client)

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        json=review_request(),
    )
    assert response.status_code == 401


def test_operator_attestation_is_advisory_only(client):
    draft_id = make_draft(client)

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        json=review_request(),
        headers=auth(),
    )

    assert response.status_code == 201
    result = response.json()
    assert result["execution_authorized"] is False

    retrieved = client.get(
        f"/api/bounty-agent/program-scopes/{draft_id}"
        f"/reviews/{result['id']}",
        headers=auth(),
    )
    assert retrieved.status_code == 200
    assert retrieved.json()["review"]["reviewer"] == "reviewer-test"
    assert retrieved.json()["execution_authorized"] is False


def test_attestation_requires_explicit_confirmation(client):
    draft_id = make_draft(client)
    payload = review_request()
    payload["source_matches"] = False

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        json=payload,
        headers=auth(),
    )

    assert response.status_code == 422


def test_browser_cannot_supply_reviewer_identity(client):
    draft_id = make_draft(client)
    payload = review_request()
    payload["reviewer"] = "forged-administrator"

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        json=payload,
        headers=auth(),
    )

    assert response.status_code == 201

    saved = client.get(
        f"/api/bounty-agent/program-scopes/{draft_id}"
        f"/reviews/{response.json()['id']}",
        headers=auth(),
    )

    assert saved.json()["review"]["reviewer"] == "reviewer-test"


def test_missing_authorization_does_not_trigger_execution(client):
    draft_id = make_draft(client)
    review = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}/reviews",
        json=review_request(),
        headers=auth(),
    )
    assert review.status_code == 201

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}"
        "/authorization-assessment",
        json={
            "review_id": review.json()["id"],
            "hostname": "api.training.example",
            "authorization_id": "nonexistent-auth",
        },
        headers=auth(),
    )

    assert response.status_code == 200
    assert response.json()["authorization_match"] is False
    assert response.json()["execution_started"] is False
    assert response.json()["execution_authorized"] is False


def test_assessment_requires_authentication(client):
    draft_id = make_draft(client)

    response = client.post(
        f"/api/bounty-agent/program-scopes/{draft_id}"
        "/authorization-assessment",
        json={
            "review_id": "missing",
            "hostname": "api.training.example",
            "authorization_id": "missing",
        },
    )

    assert response.status_code == 401

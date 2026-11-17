import base64

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import (
    require_bounty_access,
)
from core.src.routes import program_scopes_r921d


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-operator")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "test-only-password-" + "x" * 40,
    )

    app = FastAPI()
    app.include_router(
        program_scopes_r921d.router,
        prefix="/api/bounty-agent",
        dependencies=[Depends(require_bounty_access)],
    )
    return TestClient(app)


def auth():
    encoded = base64.b64encode(
        ("test-operator:test-only-password-" + "x" * 40)
        .encode()
    ).decode()
    return {"Authorization": "Basic " + encoded}


def policy():
    return {
        "platform": "hackerone",
        "program": "Synthetic Training",
        "policy_url": "https://hackerone.com/training",
        "in_scope": ["api.training.example"],
        "out_of_scope": ["admin.training.example"],
        "restrictions": ["No automated scanning"],
    }


def test_unauthenticated_listing_rejected(client):
    assert client.get(
        "/api/bounty-agent/program-scopes"
    ).status_code == 401


def test_unauthenticated_import_rejected(client):
    response = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
    )
    assert response.status_code == 401


def test_authenticated_import(client):
    response = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
        headers=auth(),
    )
    assert response.status_code == 201
    result = response.json()
    assert result["review_status"] == "unverified"
    assert result["execution_authorized"] is False


def test_import_list_and_get(client):
    created = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
        headers=auth(),
    )
    assert created.status_code == 201

    identity = created.json()["id"]

    listed = client.get(
        "/api/bounty-agent/program-scopes",
        headers=auth(),
    )

    assert listed.status_code == 200
    assert len(listed.json()["drafts"]) == 1

    retrieved = client.get(
        f"/api/bounty-agent/program-scopes/{identity}",
        headers=auth(),
    )

    assert retrieved.status_code == 200
    assert retrieved.json()["draft"]["program"] == (
        "Synthetic Training"
    )


def test_duplicate_import_idempotent(client):
    first = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
        headers=auth(),
    )
    second = client.post(
        "/api/bounty-agent/program-scopes",
        json=policy(),
        headers=auth(),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_wildcard_import_rejected(client):
    payload = policy()
    payload["in_scope"] = ["*.training.example"]

    response = client.post(
        "/api/bounty-agent/program-scopes",
        json=payload,
        headers=auth(),
    )

    assert response.status_code == 422


def test_unknown_draft_rejected(client):
    response = client.get(
        "/api/bounty-agent/program-scopes/missing",
        headers=auth(),
    )
    assert response.status_code == 404


def test_parent_router_registration(tmp_path, monkeypatch):
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from core.bounty_agent.http_access import require_bounty_access
    from core.src.routes.bounty_agent import router

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-operator")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "test-only-password-" + "x" * 40,
    )

    app = FastAPI()
    app.include_router(
        router,
        dependencies=[Depends(require_bounty_access)],
    )

    paths = app.openapi()["paths"]

    assert "/api/bounty-agent/program-scopes" in paths
    assert (
        "/api/bounty-agent/program-scopes/{draft_id}"
        in paths
    )

    client = TestClient(app)

    # Authentication must be enforced by the actual parent router.
    unauthenticated = client.get(
        "/api/bounty-agent/program-scopes"
    )
    assert unauthenticated.status_code == 401

    # Confirm authenticated requests reach the live route handler.
    authenticated = client.get(
        "/api/bounty-agent/program-scopes",
        headers=auth(),
    )
    assert authenticated.status_code == 200
    assert authenticated.json()["drafts"] == []
    assert authenticated.json()["execution_authorized"] is False

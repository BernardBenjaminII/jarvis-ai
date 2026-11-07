"""R9.12D: HTTP authentication integration tests.

Tests the same router dependency used by main.py without
importing unrelated JARVIS application services.
"""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import (
    require_bounty_access,
)
from core.src.routes import bounty_agent as routes


def make_client():
    app = FastAPI()
    app.include_router(
        routes.router,
        dependencies=[Depends(require_bounty_access)],
    )
    return TestClient(app)


def test_r912d_unconfigured_api_denied(monkeypatch):
    monkeypatch.delenv("JARVIS_BOUNTY_USER", raising=False)
    monkeypatch.delenv(
        "JARVIS_BOUNTY_PASSWORD", raising=False
    )

    with make_client() as client:
        response = client.get(
            "/api/bounty-agent/sessions"
        )

    assert response.status_code == 503


def test_r912d_missing_credentials_denied(monkeypatch):
    monkeypatch.setenv(
        "JARVIS_BOUNTY_USER", "operator"
    )
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD", "x" * 64
    )

    with make_client() as client:
        response = client.get(
            "/api/bounty-agent/sessions"
        )

    assert response.status_code == 401


def test_r912d_invalid_credentials_denied(monkeypatch):
    monkeypatch.setenv(
        "JARVIS_BOUNTY_USER", "operator"
    )
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD", "x" * 64
    )

    with make_client() as client:
        response = client.post(
            "/api/bounty-agent/sessions",
            auth=("operator", "wrong"),
            json={
                "authorization_id": "synthetic",
                "root_target": "example.com",
                "budget": 1,
            },
        )

    assert response.status_code == 401


def test_r912d_valid_credentials_reach_router(monkeypatch):
    class FakeAgent:
        def list_sessions(self, limit):
            return []

    monkeypatch.setenv(
        "JARVIS_BOUNTY_USER", "operator"
    )
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD", "x" * 64
    )
    monkeypatch.setattr(
        routes, "_agent", lambda: FakeAgent()
    )

    with make_client() as client:
        response = client.get(
            "/api/bounty-agent/sessions",
            auth=("operator", "x" * 64),
        )

    assert response.status_code == 200
    assert response.json() == {"sessions": []}

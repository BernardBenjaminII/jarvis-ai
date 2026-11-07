"""R9.15A.5 authenticated proposal API tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.src.routes.bounty_proposals import router


def client_with_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "reviewer")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "synthetic-test-password-long-enough-12345",
    )

    app = FastAPI()
    app.include_router(router)

    return TestClient(app)


def test_unauthenticated_request_rejected(
    monkeypatch, tmp_path
):
    client = client_with_auth(monkeypatch, tmp_path)

    response = client.get(
        "/api/bounty-agent/proposals"
    )

    assert response.status_code == 401


def test_authenticated_empty_queue(
    monkeypatch, tmp_path
):
    client = client_with_auth(monkeypatch, tmp_path)

    response = client.get(
        "/api/bounty-agent/proposals",
        auth=(
            "reviewer",
            "synthetic-test-password-long-enough-12345",
        ),
    )

    assert response.status_code == 200
    assert response.json() == {"proposals": []}


def test_unknown_proposal_returns_404(
    monkeypatch, tmp_path
):
    client = client_with_auth(monkeypatch, tmp_path)

    response = client.get(
        "/api/bounty-agent/proposals/nonexistent",
        auth=(
            "reviewer",
            "synthetic-test-password-long-enough-12345",
        ),
    )

    assert response.status_code == 404

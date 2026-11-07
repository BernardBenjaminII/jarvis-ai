import json
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.src.routes import bounty_agent as routes


@pytest.fixture
def client(monkeypatch):
    class FakeAgent:
        def report(self, session_id):
            return {
                "session": {
                    "id": session_id,
                    "program": "Synthetic",
                    "root_target": "example.com",
                },
                "mission": {
                    "mission": {"state": "ready"},
                    "tasks": [],
                },
                "options": [],
                "investigation_plans": [],
            }

    monkeypatch.setattr(
        routes, "_agent", lambda: FakeAgent()
    )

    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


@pytest.mark.parametrize(
    "format_name", ["json", "markdown"]
)
def test_r912c_disabled_without_configuration(
    client, monkeypatch, format_name
):
    monkeypatch.delenv(
        "JARVIS_BOUNTY_EXPORT_TOKEN", raising=False
    )

    response = client.get(
        f"/api/bounty-agent/sessions/demo/export/{format_name}"
    )

    assert response.status_code == 503


@pytest.mark.parametrize(
    "format_name", ["json", "markdown"]
)
def test_r912c_denies_missing_or_invalid_token(
    client, monkeypatch, format_name
):
    monkeypatch.setenv(
        "JARVIS_BOUNTY_EXPORT_TOKEN", "t" * 64
    )

    url = (
        "/api/bounty-agent/sessions/demo/export/"
        + format_name
    )

    assert client.get(url).status_code == 401
    assert client.get(
        url,
        headers={"X-JARVIS-Export-Token": "wrong"},
    ).status_code == 401


@pytest.mark.parametrize(
    "format_name", ["json", "markdown"]
)
def test_r912c_authorized_export(
    client, monkeypatch, format_name
):
    token = "a" * 64

    monkeypatch.setenv(
        "JARVIS_BOUNTY_EXPORT_TOKEN", token
    )

    response = client.get(
        "/api/bounty-agent/sessions/demo/export/"
        + format_name,
        headers={"X-JARVIS-Export-Token": token},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "attachment" in response.headers[
        "content-disposition"
    ]

    if format_name == "json":
        data = json.loads(response.content)
        assert data["submission_status"] == "not_submitted"
    else:
        assert b"JARVIS Bug Bounty" in response.content

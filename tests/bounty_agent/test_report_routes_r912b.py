import json

from core.src.routes import bounty_agent as routes


def synthetic_report():
    return {
        "session": {
            "id": "synthetic-session",
            "authorization": "synthetic-auth",
            "program": "Synthetic",
            "root_target": "example.com",
            "state": "recon_complete",
            "updated": 1700000000,
        },
        "mission": {
            "mission": {
                "state": "ready",
                "used": 1,
            },
            "tasks": [],
        },
        "options": [],
        "investigation_plans": [],
        "events": [],
    }


def test_r912b_json_route(monkeypatch):
    class FakeAgent:
        def report(self, session_id):
            assert session_id == "synthetic-session"
            return synthetic_report()

    monkeypatch.setattr(routes, "_agent", lambda: FakeAgent())

    response = routes.export_session_json(
        "synthetic-session"
    )

    data = json.loads(response.body)

    assert data["submission_status"] == "not_submitted"
    assert data["source"]["session"]["id"] == (
        "synthetic-session"
    )
    assert response.headers["cache-control"] == "no-store"
    assert "attachment" in response.headers[
        "content-disposition"
    ]


def test_r912b_markdown_route(monkeypatch):
    class FakeAgent:
        def report(self, session_id):
            return synthetic_report()

    monkeypatch.setattr(routes, "_agent", lambda: FakeAgent())

    response = routes.export_session_markdown(
        "synthetic-session"
    )

    text = response.body.decode("utf-8")

    assert "# JARVIS Bug Bounty Investigation" in text
    assert "Not submitted" in text
    assert "example.com" in text


def test_r912b_missing_session_fails_closed(monkeypatch):
    import pytest
    from fastapi import HTTPException

    class FakeAgent:
        def report(self, session_id):
            raise ValueError("Unknown session")

    monkeypatch.setattr(routes, "_agent", lambda: FakeAgent())

    with pytest.raises(HTTPException) as error:
        routes.export_session_json("missing")

    assert error.value.status_code == 404
    assert error.value.detail == "Report unavailable"

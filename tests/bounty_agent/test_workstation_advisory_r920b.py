from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.src.routes import bounty_agent as route_module


def test_workstation_advisory_security(monkeypatch):
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-user")
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", "T" * 40)

    monkeypatch.setattr(
        "core.bootstrap.discovery.platform.detect_platform",
        lambda: "kali",
    )

    app = FastAPI()
    app.include_router(
        route_module.router,
        dependencies=[Depends(require_bounty_access)],
    )
    client = TestClient(app)

    path = "/api/bounty-agent/workstation-advisory"

    # Authentication must be enforced.
    response = client.get(path)
    assert response.status_code == 401

    response = client.get(
        path,
        auth=("test-user", "incorrect-password"),
    )
    assert response.status_code == 401

    # Valid credentials may read the advisory.
    response = client.get(
        path,
        auth=("test-user", "T" * 40),
    )
    assert response.status_code == 200, response.text

    data = response.json()

    assert data["version"] == "r920a"
    assert data["mode"] == "advisory_only"
    assert data["execution_authorized"] is False
    assert data["submission_authorized"] is False

    assert len(data["activities"]) == 6
    assert len(data["legacy_lab_experiments"]) == 5

    assert all(
        item["execution_allowed"] is False
        and item["human_review_required"] is True
        for item in data["activities"].values()
    )

    assert all(
        item["execution_allowed"] is False
        for item in data["legacy_lab_experiments"].values()
    )


def test_workstation_advisory_non_kali(monkeypatch):
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-user")
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", "T" * 40)

    monkeypatch.setattr(
        "core.bootstrap.discovery.platform.detect_platform",
        lambda: "ubuntu",
    )

    app = FastAPI()
    app.include_router(
        route_module.router,
        dependencies=[Depends(require_bounty_access)],
    )

    response = TestClient(app).get(
        "/api/bounty-agent/workstation-advisory",
        auth=("test-user", "T" * 40),
    )
    assert response.status_code == 404


def test_workstation_advisory_missing_auth_config(monkeypatch):
    monkeypatch.delenv("JARVIS_BOUNTY_USER", raising=False)
    monkeypatch.delenv("JARVIS_BOUNTY_PASSWORD", raising=False)

    app = FastAPI()
    app.include_router(
        route_module.router,
        dependencies=[Depends(require_bounty_access)],
    )

    response = TestClient(app).get(
        "/api/bounty-agent/workstation-advisory"
    )
    assert response.status_code == 503

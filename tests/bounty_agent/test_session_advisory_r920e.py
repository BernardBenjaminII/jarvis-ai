"""R9.20E: synthetic session advisory security tests."""

from copy import deepcopy

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.src.routes import bounty_agent as routes


PATH = "/api/bounty-agent/sessions/session-test/mission-advisory"
PASSWORD = "T" * 40


class Scope:
    program = "training"
    logical_capabilities = (
        "subdomain_discovery",
        "dns_resolution",
        "http_probe",
    )

    def permits_host(self, host):
        return host == "training.example"

    def require(self, host, tool):
        if not self.permits_host(host):
            raise ValueError("Target outside scope")
        if tool not in {"subfinder", "dnsx", "httpx"}:
            raise ValueError("Tool not authorized")


class Store:
    expired = False

    def live_scope(self, authorization_id):
        if self.expired or authorization_id != "auth-test":
            raise ValueError("Authorization unavailable")
        return Scope()


class Agent:
    def __init__(self):
        self.authorization_store = Store()
        self.session = {
            "id": "session-test",
            "mission": "mission-test",
            "authorization": "auth-test",
            "program": "training",
            "root_target": "training.example",
        }
        self.mission = {
            "id": "mission-test",
            "budget": 3,
        }

    def report(self, session_id):
        if session_id != "session-test":
            raise ValueError("Unknown session")
        return {
            "session": deepcopy(self.session),
            "mission": {
                "mission": deepcopy(self.mission)
            },
        }


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-user")
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", PASSWORD)

    monkeypatch.setattr(
        "core.bootstrap.discovery.platform.detect_platform",
        lambda: "kali",
    )

    monkeypatch.setattr(
        "core.bounty_agent.autonomy.mission_advisory_r920d.inventory",
        lambda: {
            "subfinder": {"executable_present": True},
            "dnsx": {"executable_present": True},
            "httpx": {"recon_available": True},
        },
    )

    agent = Agent()
    monkeypatch.setattr(routes, "_agent", lambda: agent)

    app = FastAPI()
    app.include_router(
        routes.router,
        dependencies=[Depends(require_bounty_access)],
    )

    return TestClient(app), agent


def authorized_get(client, path=PATH):
    return client.get(
        path,
        auth=("test-user", PASSWORD),
    )


def test_authentication_required(setup):
    client, _ = setup
    assert client.get(PATH).status_code == 401


def test_valid_session_advisory(setup):
    client, _ = setup
    response = authorized_get(client)

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["session_id"] == "session-test"
    assert data["mission_id"] == "mission-test"
    assert data["target"] == "training.example"
    assert data["authorization_checked"] is True
    assert data["execution_authorized"] is False
    assert data["execution_started"] is False
    assert data["automatic_execution_allowed"] is False
    assert data["submission_authorized"] is False
    assert data["human_review_required"] is True
    assert len(data["recommended_tasks"]) == 3


def test_unknown_session(setup):
    client, _ = setup
    response = authorized_get(
        client,
        "/api/bounty-agent/sessions/unknown/mission-advisory",
    )
    assert response.status_code == 404


def test_session_identity_mismatch(setup):
    client, agent = setup
    agent.session["id"] = "another-session"
    assert authorized_get(client).status_code == 404


def test_mission_identity_mismatch(setup):
    client, agent = setup
    agent.mission["id"] = "different-mission"
    assert authorized_get(client).status_code == 404


def test_expired_or_invalid_authorization(setup):
    client, agent = setup
    agent.authorization_store.expired = True
    assert authorized_get(client).status_code == 409


def test_real_world_target_rejected(setup):
    client, agent = setup
    agent.session["root_target"] = "example.com"
    assert authorized_get(client).status_code == 409


def test_program_mismatch_rejected(setup):
    client, agent = setup
    agent.session["program"] = "different-program"
    assert authorized_get(client).status_code == 409


def test_budget_capped(setup):
    client, agent = setup
    agent.mission["budget"] = 100

    response = authorized_get(client)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["original_mission_budget"] == 100
    assert data["planning_budget_capped"] is True
    assert data["budget"] == 10
    assert data["execution_authorized"] is False


def test_non_kali_rejected(setup, monkeypatch):
    client, _ = setup
    monkeypatch.setattr(
        "core.bootstrap.discovery.platform.detect_platform",
        lambda: "ubuntu",
    )
    assert authorized_get(client).status_code == 404

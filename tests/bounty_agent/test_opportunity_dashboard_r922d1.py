"""R9.22D1 authenticated, read-only dashboard API tests."""

import json
import time

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.capabilities.kali_workstation import TOOLS
from core.src.routes import bounty_agent
from core.src.routes import bounty_opportunities_r922d1 as dashboard
from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
)
from core.bounty_catalog.store import Catalog


AUTH = ("test-user", "T" * 40)


def make_client(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_BOUNTY_USER", AUTH[0])
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", AUTH[1])
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("JARVIS_RUNTIME_ROOT", str(tmp_path / "runtime"))

    monkeypatch.setattr(
        dashboard,
        "inventory_snapshot",
        lambda: {
            "state": "ready",
            "mode": "inventory_only",
            "execution_authorized": False,
            "tool_count": len(TOOLS),
            "installed_count": len(TOOLS),
            "tools": {
                name: {
                    "installed": True,
                    "path": f"/usr/bin/{name}",
                }
                for name in TOOLS
            },
        },
    )

    app = FastAPI()
    app.include_router(
        bounty_agent.router,
        dependencies=[Depends(require_bounty_access)],
    )

    return TestClient(app)


PATH = "/api/bounty-agent/opportunity-intelligence"


def test_authentication_required(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    assert client.get(PATH).status_code == 401
    assert client.get(
        PATH, auth=("test-user", "wrong")
    ).status_code == 401


def test_missing_databases_are_not_created(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    response = client.get(PATH, auth=AUTH)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["opportunity_count"] == 0
    assert data["sources"]["hackerone_catalog"]["status"] == "missing"
    assert data["automatic_execution_allowed"] is False
    assert data["mission_creation_allowed"] is False

    assert not (
        tmp_path / "xdg/jarvis/program_scopes_r921d.sqlite3"
    ).exists()
    assert not (
        tmp_path / "runtime/bounty_catalog/r4.sqlite"
    ).exists()


def test_imported_policy_is_review_only(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    store = ProgramScopeStore(
        tmp_path / "xdg/jarvis/program_scopes_r921d.sqlite3"
    )

    store.import_draft(
        create_scope_draft(
            platform="bugcrowd",
            program="Synthetic Training",
            policy_url="https://bugcrowd.com/engagements/training",
            in_scope=["api.training.example"],
            out_of_scope=[],
            restrictions=["No automated scanning"],
        )
    )

    response = client.get(PATH, auth=AUTH)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["opportunity_count"] == 1
    assert data["imported_policy_count"] == 1

    item = data["opportunities"][0]
    assert item["source"] == "manual_policy_import"
    assert item["testing_authorized"] is False
    assert item["human_review_required"] is True


def test_existing_hackerone_catalog(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    catalog = Catalog(
        tmp_path / "runtime/bounty_catalog/r4.sqlite"
    )

    raw = json.dumps({
        "data": [{
            "type": "program",
            "attributes": {
                "handle": "synthetic-training",
                "name": "Synthetic Training",
                "offers_bounties": True,
                "submission_state": "open",
                "state": "public_mode",
                "policy": "Synthetic data. No testing permission.",
            },
        }],
        "links": {},
    }).encode()

    observed = time.time()
    catalog.save(
        "hackerone-api",
        observed,
        [(1, raw, observed)],
        "complete",
    )

    response = client.get(PATH, auth=AUTH)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["sources"]["hackerone_catalog"]["status"] == "fresh"
    assert data["opportunity_count"] == 1
    assert data["network_requests"] == 0
    assert data["opportunities"][0]["testing_authorized"] is False


def test_unsafe_result_fails_closed(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    monkeypatch.setattr(
        dashboard,
        "rank_opportunity_reviews",
        lambda *_: {
            "network_requests": 0,
            "testing_authorized": True,
            "automatic_execution_allowed": False,
            "mission_creation_allowed": False,
            "submission_authorized": False,
        },
    )

    response = client.get(PATH, auth=AUTH)
    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Opportunity intelligence unavailable"
    )

def test_existing_scope_database_is_read_only(
    tmp_path, monkeypatch
):
    client = make_client(tmp_path, monkeypatch)

    db_path = (
        tmp_path / "xdg/jarvis/program_scopes_r921d.sqlite3"
    )

    store = ProgramScopeStore(db_path)

    store.import_draft(
        create_scope_draft(
            platform="hackerone",
            program="Synthetic Read Only Test",
            policy_url="https://hackerone.com/training",
            in_scope=["api.training.example"],
            out_of_scope=[],
            restrictions=["No automated scanning"],
        )
    )

    before = db_path.read_bytes()

    # The dashboard must never call the mutable constructor.
    def forbidden_constructor(*args, **kwargs):
        raise AssertionError(
            "Mutable ProgramScopeStore initialization attempted"
        )

    monkeypatch.setattr(
        ProgramScopeStore,
        "__init__",
        forbidden_constructor,
    )

    response = client.get(PATH, auth=AUTH)

    assert response.status_code == 200, response.text
    assert response.json()["imported_policy_count"] == 1
    assert db_path.read_bytes() == before

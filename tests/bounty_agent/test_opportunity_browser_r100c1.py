"""R10.0C1 authenticated offline opportunity browser tests."""

import json
import time

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.capabilities.kali_workstation import TOOLS
from core.bounty_catalog.store import Catalog
from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
)
from core.src.routes import bounty_agent
from core.src.routes import bounty_opportunities_r922d1 as browser


AUTH = ("test-operator", "T" * 40)
URL = "/api/bounty-agent/opportunities"


def setup_client(tmp_path, monkeypatch, seeded=True):
    runtime = tmp_path / "runtime"
    xdg = tmp_path / "xdg"

    monkeypatch.setenv("JARVIS_RUNTIME_ROOT", str(runtime))
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", AUTH[0])
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", AUTH[1])

    monkeypatch.setattr(
        browser,
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
                    "path": "/usr/bin/" + name,
                }
                for name in TOOLS
            },
        },
    )

    if seeded:
        catalog = Catalog(
            runtime / "bounty_catalog/r4.sqlite"
        )

        raw = json.dumps({
            "data": [
                {
                    "type": "program",
                    "attributes": {
                        "handle": handle,
                        "name": name,
                        "offers_bounties": paid,
                        "submission_state": "open",
                        "state": "public_mode",
                        "policy": "Synthetic policy only.",
                    },
                }
                for handle, name, paid in (
                    ("alpha-lab", "Alpha Lab", True),
                    ("beta-lab", "Beta Lab", True),
                    ("gamma-lab", "Gamma Lab", False),
                )
            ],
            "links": {},
        }).encode()

        now = time.time()

        catalog.save(
            "hackerone-api",
            now,
            [(1, raw, now)],
            "complete",
        )

        store = ProgramScopeStore(
            xdg / "jarvis/program_scopes_r921d.sqlite3"
        )

        store.import_draft(
            create_scope_draft(
                platform="bugcrowd",
                program="Imported Synthetic",
                policy_url=(
                    "https://bugcrowd.com/engagements/training"
                ),
                in_scope=["api.training.example"],
                out_of_scope=[],
                restrictions=["No automated scanning"],
            )
        )

    app = FastAPI()

    app.include_router(
        bounty_agent.router,
        dependencies=[Depends(require_bounty_access)],
    )

    return TestClient(app), runtime, xdg


def test_browser_requires_auth(tmp_path, monkeypatch):
    client, _, _ = setup_client(tmp_path, monkeypatch)

    assert client.get(URL).status_code == 401
    assert client.get(
        URL, auth=("test-operator", "wrong")
    ).status_code == 401


def test_pagination_returns_all_records_without_overlap(
    tmp_path, monkeypatch
):
    client, _, _ = setup_client(tmp_path, monkeypatch)

    first = client.get(
        URL, auth=AUTH, params={"limit": 2}
    )

    second = client.get(
        URL, auth=AUTH,
        params={"limit": 2, "offset": 2},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    a = first.json()
    b = second.json()

    assert a["schema"] == (
        "jarvis.bounty.opportunity_browser.r10c1"
    )
    assert a["total_opportunities"] == 4
    assert a["total_matched"] == 4
    assert a["returned_count"] == 2
    assert a["has_more"] is True

    assert b["returned_count"] == 2
    assert b["has_more"] is False

    identities = {
        (item["source"], item["source_identifier"])
        for item in a["results"] + b["results"]
    }

    assert len(identities) == 4


def test_search_and_filters(tmp_path, monkeypatch):
    client, _, _ = setup_client(tmp_path, monkeypatch)

    alpha = client.get(
        URL, auth=AUTH,
        params={"search": "ALPHA"},
    ).json()

    imported = client.get(
        URL, auth=AUTH,
        params={"source": "manual_policy_import"},
    ).json()

    lane = client.get(
        URL, auth=AUTH,
        params={"lane": "IMPORTED_POLICY"},
    ).json()

    missing = client.get(
        URL, auth=AUTH,
        params={"search": "does-not-exist"},
    ).json()

    assert alpha["total_matched"] == 1
    assert alpha["results"][0]["program"] == "Alpha Lab"

    assert imported["total_matched"] == 1
    assert imported["results"][0]["program"] == (
        "Imported Synthetic"
    )

    assert lane["total_matched"] == 1
    assert missing["total_matched"] == 0


def test_invalid_filters_are_rejected(
    tmp_path, monkeypatch
):
    client, _, _ = setup_client(tmp_path, monkeypatch)

    for params in (
        {"source": "untrusted"},
        {"lane": "AUTHORIZED"},
        {"limit": 0},
        {"limit": 201},
        {"offset": -1},
        {"search": "X" * 121},
    ):
        response = client.get(
            URL, auth=AUTH, params=params
        )
        assert response.status_code == 422


def test_browser_never_creates_missing_databases(
    tmp_path, monkeypatch
):
    client, runtime, xdg = setup_client(
        tmp_path, monkeypatch, seeded=False
    )

    response = client.get(URL, auth=AUTH)

    assert response.status_code == 200, response.text
    assert response.json()["total_opportunities"] == 0

    assert not (
        runtime / "bounty_catalog/r4.sqlite"
    ).exists()

    assert not (
        xdg / "jarvis/program_scopes_r921d.sqlite3"
    ).exists()


def test_browser_does_not_modify_stored_evidence(
    tmp_path, monkeypatch
):
    client, runtime, xdg = setup_client(
        tmp_path, monkeypatch
    )

    catalog = runtime / "bounty_catalog/r4.sqlite"
    scopes = xdg / "jarvis/program_scopes_r921d.sqlite3"

    before_catalog = catalog.read_bytes()
    before_scopes = scopes.read_bytes()

    response = client.get(
        URL, auth=AUTH,
        params={"search": "lab", "limit": 1},
    )

    assert response.status_code == 200, response.text

    assert catalog.read_bytes() == before_catalog
    assert scopes.read_bytes() == before_scopes

    result = response.json()

    assert result["network_requests"] == 0
    assert result["testing_authorized"] is False
    assert result["automatic_execution_allowed"] is False
    assert result["mission_creation_allowed"] is False


def test_unsafe_ranked_record_fails_closed(
    tmp_path, monkeypatch
):
    client, _, _ = setup_client(tmp_path, monkeypatch)

    original = browser.get_opportunity_intelligence(
        limit=200
    )

    original["opportunities"][0][
        "testing_authorized"
    ] = True

    monkeypatch.setattr(
        browser,
        "get_opportunity_intelligence",
        lambda limit=200: original,
    )

    response = client.get(URL, auth=AUTH)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unsafe opportunity record"
    )

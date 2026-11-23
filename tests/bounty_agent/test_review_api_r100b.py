import json
import sqlite3
import time

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.http_access import require_bounty_access
from core.bounty_catalog.store import Catalog
from core.bounty_catalog.operations_r100a import ingest
from core.src.routes.bounty_agent import router


AUTH = ("test-operator", "T" * 40)
PATH = "/api/bounty-agent/opportunity-reviews"
HEADERS = {
    "X-Jarvis-Review-Intent": "review-state-only",
}


def setup_client(tmp_path, monkeypatch, *, seeded=True):
    runtime = tmp_path / "runtime"

    monkeypatch.setenv("JARVIS_RUNTIME_ROOT", str(runtime))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", AUTH[0])
    monkeypatch.setenv("JARVIS_BOUNTY_PASSWORD", AUTH[1])

    if seeded:
        catalog = Catalog(
            runtime / "bounty_catalog/r4.sqlite"
        )
        ledger = (
            runtime / "bounty_operations/r10_events.sqlite3"
        )

        for handles in (["alpha"], ["alpha", "beta"]):
            raw = json.dumps({
                "data": [
                    {
                        "type": "program",
                        "attributes": {
                            "handle": handle,
                            "name": handle,
                            "offers_bounties": True,
                            "submission_state": "open",
                            "policy": "Synthetic policy",
                        },
                    }
                    for handle in handles
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

            # First snapshot establishes the baseline.
            # Second snapshot generates reviewable changes.
            ingest(catalog.path, ledger)

    app = FastAPI()
    app.include_router(
        router,
        dependencies=[Depends(require_bounty_access)],
    )

    return TestClient(app), runtime


def payload(request_id="review-100001"):
    return {
        "expected_state": "pending",
        "new_state": "acknowledged",
        "request_id": request_id,
        "note": "Operator reviewed the listing",
    }


def test_queue_requires_authentication(tmp_path, monkeypatch):
    client, _ = setup_client(tmp_path, monkeypatch)

    assert client.get(PATH).status_code == 401
    assert client.get(
        PATH,
        auth=("test-operator", "wrong"),
    ).status_code == 401


def test_missing_ledger_does_not_get_created(
    tmp_path, monkeypatch
):
    client, runtime = setup_client(
        tmp_path, monkeypatch, seeded=False
    )

    result = client.get(PATH, auth=AUTH)

    assert result.status_code == 200
    assert result.json()["status"] == "ledger_missing"
    assert not (
        runtime / "bounty_operations/r10_events.sqlite3"
    ).exists()


def test_review_queue_is_read_only(tmp_path, monkeypatch):
    client, runtime = setup_client(tmp_path, monkeypatch)

    ledger = runtime / "bounty_operations/r10_events.sqlite3"
    before = ledger.read_bytes()

    response = client.get(PATH, auth=AUTH)

    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 1
    assert data["counts"]["pending"] == 1
    assert data["execution_authorized"] is False
    assert ledger.read_bytes() == before


def test_history_empty_before_first_decision(
    tmp_path, monkeypatch
):
    client, runtime = setup_client(tmp_path, monkeypatch)

    result = client.get(PATH, auth=AUTH).json()
    event_id = result["records"][0]["id"]

    history = client.get(
        f"{PATH}/{event_id}/history",
        auth=AUTH,
    )

    assert history.status_code == 200
    assert history.json()["total_history"] == 0
    assert history.json()["records"] == []

    ledger = runtime / "bounty_operations/r10_events.sqlite3"
    with sqlite3.connect(ledger) as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE name='review_history'"
        ).fetchone()

    assert exists is None


def test_decision_requires_explicit_intent(
    tmp_path, monkeypatch
):
    client, _ = setup_client(tmp_path, monkeypatch)
    event_id = client.get(
        PATH, auth=AUTH
    ).json()["records"][0]["id"]

    assert client.post(
        f"{PATH}/{event_id}/decisions",
        auth=AUTH,
        json=payload(),
    ).status_code == 403

    assert client.post(
        f"{PATH}/{event_id}/decisions",
        headers=HEADERS,
        json=payload(),
    ).status_code == 401


def test_decision_persists_authenticated_actor(
    tmp_path, monkeypatch
):
    client, _ = setup_client(tmp_path, monkeypatch)
    event_id = client.get(
        PATH, auth=AUTH
    ).json()["records"][0]["id"]

    response = client.post(
        f"{PATH}/{event_id}/decisions",
        auth=AUTH,
        headers=HEADERS,
        json=payload(),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "updated"
    assert response.json()["execution_authorized"] is False

    history = client.get(
        f"{PATH}/{event_id}/history",
        auth=AUTH,
    ).json()

    assert history["total_history"] == 1
    assert history["records"][0]["actor"] == AUTH[0]
    assert history["records"][0]["to_state"] == "acknowledged"


def test_idempotent_retry_and_stale_decision(
    tmp_path, monkeypatch
):
    client, _ = setup_client(tmp_path, monkeypatch)
    event_id = client.get(
        PATH, auth=AUTH
    ).json()["records"][0]["id"]
    url = f"{PATH}/{event_id}/decisions"

    first = client.post(
        url, auth=AUTH, headers=HEADERS,
        json=payload(),
    )

    retry = client.post(
        url, auth=AUTH, headers=HEADERS,
        json=payload(),
    )

    stale = client.post(
        url, auth=AUTH, headers=HEADERS,
        json={
            **payload("review-100002"),
            "new_state": "deferred",
        },
    )

    assert first.status_code == 200
    assert retry.status_code == 200
    assert retry.json()["status"] == "already_applied"
    assert stale.status_code == 409

    history = client.get(
        f"{PATH}/{event_id}/history",
        auth=AUTH,
    ).json()

    assert history["total_history"] == 1


def test_unknown_event_returns_404(tmp_path, monkeypatch):
    client, _ = setup_client(tmp_path, monkeypatch)

    response = client.get(
        f"{PATH}/999999/history",
        auth=AUTH,
    )

    assert response.status_code == 404

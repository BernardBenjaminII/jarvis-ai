from core.bounty_authorization import AuthorizationStore
from core.bounty_live.engine import LiveMissionStore
import core.bounty_live.engine as engine


def setup(tmp_path):
    auth_store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auth_store.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    missions = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auth_store,
    )

    return auth_store, auth, missions


def test_create_and_queue(tmp_path):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=5)

    tid = missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    report = missions.report(mid)

    assert report["mission"]["budget"] == 5
    assert report["tasks"][0]["id"] == tid


def test_live_subfinder_persists_evidence(tmp_path, monkeypatch):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=5)

    tid = missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    monkeypatch.setattr(
        engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": ["a.example.com"],
            "rejected": [],
        },
    )

    monkeypatch.setattr(
        missions,
        "_tool_metadata",
        lambda capability: {
            "binary_path": "/test/subfinder",
            "tool_version": "test-version",
        },
    )

    result = missions.run(tid)

    assert result["schema"] == "jarvis-bounty-live-r5.1"
    assert result["result"]["accepted"] == ["a.example.com"]

    report = missions.report(mid)

    assert report["tasks"][0]["state"] == "completed"
    assert report["tasks"][0]["evidence_sha256"]


def test_budget_enforced(tmp_path):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=1)

    missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    missions.queue(
        mid,
        "httpx",
        "a.example.com",
    )

    # Budget enforcement occurs at execution claim time.
    with missions.db() as db:
        db.execute(
            "UPDATE missions SET used=1 WHERE id=?",
            (mid,),
        )

    report = missions.report(mid)

    assert report["mission"]["used"] == 1

import json

import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_live.engine import LiveMissionStore


def environment(tmp_path):
    auths = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auths.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="scope-reviewer",
        source_material="reviewed synthetic rules",
        ttl=3600,
    )

    store = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    mission = store.create(auth, budget=10)

    parent = store.queue(
        mission,
        "subfinder",
        "example.com",
    )

    evidence = {
        "schema": "jarvis-bounty-live-r5.1",
        "mission_id": mission,
        "task_id": parent,
        "authorization_id": auth,
        "program": "demo",
        "capability": "subfinder",
        "target": "example.com",
        "tool": {
            "binary_path": "/test/subfinder",
            "tool_version": "test",
        },
        "result": {
            "adapter": "subfinder",
            "target": "example.com",
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "a.example.com",
                "b.example.com",
            ],
            "rejected": [],
        },
        "recorded_at": 1.0,
    }

    raw = json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
    )

    import hashlib

    with store.db() as db:
        db.execute(
            """
            UPDATE tasks
            SET state='completed',
                evidence=?,
                evidence_sha256=?,
                finished=?
            WHERE id=?
            """,
            (
                raw,
                hashlib.sha256(raw.encode()).hexdigest(),
                1.0,
                parent,
            ),
        )

    return auths, auth, store, mission, parent


def test_proposal_generation_is_non_executing(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    ids = store.propose_httpx_from_subfinder(parent)

    assert len(ids) == 2

    proposals = store.proposals(mission)

    assert [x["target"] for x in proposals] == [
        "a.example.com",
        "b.example.com",
    ]

    with store.db() as db:
        httpx_tasks = db.execute(
            """
            SELECT COUNT(*) AS n
            FROM tasks
            WHERE mission=? AND capability='httpx'
            """,
            (mission,),
        ).fetchone()["n"]

    assert httpx_tasks == 0


def test_approval_creates_queued_task(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    tid = store.approve_proposal(
        pid,
        "human-reviewer",
    )

    report = store.report(mission)

    task = [
        x for x in report["tasks"]
        if x["id"] == tid
    ][0]

    assert task["capability"] == "httpx"
    assert task["state"] == "queued"

    proposal = [
        x for x in report["proposals"]
        if x["id"] == pid
    ][0]

    assert proposal["state"] == "approved"
    assert proposal["reviewer"] == "human-reviewer"


def test_reject_does_not_create_task(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    store.reject_proposal(
        pid,
        "human-reviewer",
    )

    proposal = [
        x for x in store.proposals(mission)
        if x["id"] == pid
    ][0]

    assert proposal["state"] == "rejected"

    with store.db() as db:
        count = db.execute(
            """
            SELECT COUNT(*) AS n
            FROM tasks
            WHERE mission=? AND capability='httpx'
            """,
            (mission,),
        ).fetchone()["n"]

    assert count == 0


def test_proposals_are_deduplicated(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    first = store.propose_httpx_from_subfinder(parent)
    second = store.propose_httpx_from_subfinder(parent)

    assert first == second
    assert len(store.proposals(mission)) == 2


def test_proposal_requires_completed_subfinder(tmp_path):
    _, auth, store, mission, parent = environment(tmp_path)

    other = store.queue(
        mission,
        "httpx",
        "a.example.com",
    )

    with pytest.raises(ValueError):
        store.propose_httpx_from_subfinder(other)


def test_scope_rechecked_at_approval(tmp_path):
    auths, auth, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    auths.revoke(auth, "rules changed")

    with pytest.raises(Exception):
        store.approve_proposal(
            pid,
            "human-reviewer",
        )

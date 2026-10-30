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


def test_r912_execution_limit_is_stage_aware(
    tmp_path,
):
    auth_store = AuthorizationStore(
        tmp_path / "auth-r912.sqlite"
    )

    auth = auth_store.create(
        program="r912",
        include=[
            "example.com",
            "*.example.com",
        ],
        logical_capabilities=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        reviewer="tester",
        source_material="r912 fixture",
        ttl=3600,
    )

    missions = LiveMissionStore(
        tmp_path / "live-r912.sqlite",
        authorization_store=auth_store,
    )

    mid = missions.create(
        auth,
        budget=20,
    )

    report = missions.report(mid)
    mission = report["mission"]
    scope = auth_store.live_scope(auth)

    assert mission["budget"] == 20

    assert (
        missions._execution_limit(
            mission,
            scope,
        )
        == 41
    )


def test_r911_concurrent_claim_executes_only_once(
    tmp_path, monkeypatch
):
    """Two workers must never execute the same task."""
    import threading
    from concurrent.futures import ThreadPoolExecutor

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    entered = threading.Event()
    release = threading.Event()
    calls = []

    def fake_discovery(scope, target, cancel=None):
        calls.append(target)
        entered.set()
        assert release.wait(timeout=5)
        return {
            "state": "completed",
            "returncode": 0,
            "accepted": [],
            "rejected": [],
        }

    monkeypatch.setattr(
        engine, "enumerate_subdomains", fake_discovery
    )
    monkeypatch.setattr(
        missions, "_tool_metadata",
        lambda capability: {
            "binary_path": "/test/subfinder",
            "tool_version": "fixture",
        },
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(missions.run, task)
        try:
            assert entered.wait(timeout=5)

            # First worker has claimed the task but has
            # not yet completed its simulated execution.
            import pytest
            with pytest.raises(ValueError):
                missions.run(task)
        finally:
            release.set()

        result = first.result(timeout=5)

    assert result["result"]["state"] == "completed"
    assert calls == ["example.com"]

    report = missions.report(mission)
    assert report["mission"]["used"] == 1

    matching = [
        item for item in report["tasks"]
        if item["id"] == task
    ]
    assert len(matching) == 1
    assert matching[0]["state"] == "completed"


def test_r911b_adapter_exception_finalizes_failed(
    tmp_path, monkeypatch
):
    """An adapter exception must not strand a running task."""
    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    def broken_adapter(scope, target, cancel=None):
        raise RuntimeError("synthetic private detail")

    monkeypatch.setattr(
        engine, "enumerate_subdomains", broken_adapter
    )
    monkeypatch.setattr(
        missions, "_tool_metadata",
        lambda capability: {
            "binary_path": "/test/subfinder",
            "tool_version": "fixture",
        },
    )

    evidence = missions.run(task)

    assert evidence["result"]["state"] == "failed"
    assert evidence["result"]["error_type"] == "RuntimeError"

    report = missions.report(mission)
    matching = [
        item for item in report["tasks"]
        if item["id"] == task
    ]

    assert matching[0]["state"] == "failed"
    assert matching[0]["finished"] is not None
    assert matching[0]["evidence_sha256"]
    assert report["mission"]["used"] == 1

    # Raw exception contents must not leak into evidence.
    assert "synthetic private detail" not in str(evidence)


def test_r911c_revocation_during_execution(
    tmp_path, monkeypatch
):
    """Revoked tasks must never commit discovery evidence."""
    import pytest
    from core.bounty_authorization import AuthorizationDenied

    auths, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    monkeypatch.setattr(
        missions, "_tool_metadata",
        lambda capability: {
            "binary_path": "/test/subfinder",
            "tool_version": "fixture",
        },
    )

    def revoke_during_execution(scope, target, cancel=None):
        auths.revoke(auth, "synthetic test revocation")
        return {
            "state": "completed",
            "returncode": 0,
            "accepted": ["a.example.com"],
            "rejected": [],
        }

    monkeypatch.setattr(
        engine, "enumerate_subdomains",
        revoke_during_execution,
    )

    with pytest.raises(AuthorizationDenied):
        missions.run(task)

    report = missions.report(mission)
    matching = [
        row for row in report["tasks"]
        if row["id"] == task
    ]

    assert len(matching) == 1
    assert matching[0]["state"] == "failed"
    assert matching[0]["finished"] is not None
    assert matching[0]["evidence"] is None
    assert matching[0]["evidence_sha256"] is None
    assert report["mission"]["used"] == 1


def test_r911d_identifies_stale_running_tasks_without_mutation(
    tmp_path,
):
    """Identify suspicious execution without changing its state."""
    _, auth, missions = setup(tmp_path)

    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    with missions.db() as db:
        db.execute(
            """
            UPDATE tasks
            SET state='running', started=1000
            WHERE id=?
            """,
            (task,),
        )

    candidates = missions.interrupted_candidates(
        older_than=300, now=1400
    )

    assert len(candidates) == 1
    assert candidates[0]["id"] == task
    assert candidates[0]["age_seconds"] == 400
    assert candidates[0]["recovery_status"] == (
        "requires_operator_review"
    )

    assert missions.interrupted_candidates(
        older_than=500, now=1400
    ) == []

    with missions.db() as db:
        row = db.execute(
            "SELECT state FROM tasks WHERE id=?",
            (task,),
        ).fetchone()

    assert row["state"] == "running"


def test_r911d_rejects_invalid_threshold(tmp_path):
    import pytest

    _, _, missions = setup(tmp_path)

    for value in (0, -1, 86401, float("nan"), True):
        with pytest.raises(ValueError):
            missions.interrupted_candidates(
                older_than=value
            )


def test_r911e_manual_quarantine_preserves_budget(tmp_path):
    import pytest

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    # Simulate an abandoned task without executing a tool.
    with missions.db() as db:
        db.execute(
            "UPDATE tasks SET state='running', started=1000 "
            "WHERE id=?",
            (task,),
        )
        db.execute(
            "UPDATE missions SET used=1 WHERE id=?",
            (mission,),
        )

    with pytest.raises(ValueError):
        missions.quarantine_interrupted(
            task,
            reviewer="tester",
            now=1400,
        )

    result = missions.quarantine_interrupted(
        task,
        reviewer="tester",
        termination_confirmed=True,
        older_than=300,
        now=1400,
    )

    assert result["state"] == "interrupted"
    assert result["retry_automatically"] is False

    report = missions.report(mission)
    assert report["mission"]["used"] == 1

    with missions.db() as db:
        row = db.execute(
            "SELECT state, finished FROM tasks WHERE id=?",
            (task,),
        ).fetchone()
        event = db.execute(
            "SELECT kind FROM events "
            "WHERE mission=? ORDER BY id DESC LIMIT 1",
            (mission,),
        ).fetchone()

    assert row["state"] == "interrupted"
    assert row["finished"] == 1400
    assert event["kind"] == "interrupted_quarantined"

    with pytest.raises(ValueError):
        missions.quarantine_interrupted(
            task,
            reviewer="tester",
            termination_confirmed=True,
            now=1500,
        )

    # An interrupted task must not be executed again.
    with pytest.raises(ValueError):
        missions.run(task)


def test_r911e_refuses_nonstale_quarantine(tmp_path):
    import pytest

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    with missions.db() as db:
        db.execute(
            "UPDATE tasks SET state='running', started=1200 "
            "WHERE id=?",
            (task,),
        )

    with pytest.raises(ValueError):
        missions.quarantine_interrupted(
            task,
            reviewer="tester",
            termination_confirmed=True,
            older_than=300,
            now=1400,
        )


def test_r911f2_persists_execution_owner(
    tmp_path, monkeypatch
):
    import os
    from core.bounty_worker.process_identity import (
        current_identity,
    )

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    monkeypatch.setattr(
        engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "state": "completed",
            "returncode": 0,
            "accepted": [],
            "rejected": [],
        },
    )

    monkeypatch.setattr(
        missions,
        "_tool_metadata",
        lambda capability: {
            "binary_path": "/fixture/subfinder",
            "tool_version": "test",
        },
    )

    missions.run(task)

    with missions.db() as db:
        row = db.execute(
            "SELECT * FROM tasks WHERE id=?",
            (task,),
        ).fetchone()

    owner = current_identity()

    assert row["state"] == "completed"
    assert row["owner_pid"] == os.getpid()
    assert row["owner_boot_id"] == owner["boot_id"]
    assert row["owner_start_ticks"] == owner["start_ticks"]
    assert row["owner_started"] is not None


def test_r911f3_live_owner_status(tmp_path, monkeypatch):
    from core.bounty_worker.process_identity import (
        current_identity,
    )

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    owner = current_identity()

    with missions.db() as db:
        db.execute(
            """
            UPDATE tasks
            SET state='running',
                started=1000,
                owner_pid=?,
                owner_boot_id=?,
                owner_start_ticks=?,
                owner_started=1000
            WHERE id=?
            """,
            (
                owner["pid"],
                owner["boot_id"],
                owner["start_ticks"],
                task,
            ),
        )

    status = missions.execution_owner_status(task)

    assert status["owner_status"] == "same_process"
    assert status["child_processes_confirmed_stopped"] is False
    assert status["automatic_retry_allowed"] is False


def test_r911f3_replaced_owner_status(tmp_path):
    from core.bounty_worker.process_identity import (
        current_identity,
    )

    _, auth, missions = setup(tmp_path)
    mission = missions.create(auth, budget=5)
    task = missions.queue(
        mission, "subfinder", "example.com"
    )

    owner = current_identity()

    with missions.db() as db:
        db.execute(
            """
            UPDATE tasks
            SET state='running',
                started=1000,
                owner_pid=?,
                owner_boot_id=?,
                owner_start_ticks=?,
                owner_started=1000
            WHERE id=?
            """,
            (
                owner["pid"],
                owner["boot_id"],
                owner["start_ticks"] + 1,
                task,
            ),
        )

    status = missions.execution_owner_status(task)

    assert status["owner_status"] == (
        "absent_or_replaced"
    )
    assert status["automatic_retry_allowed"] is False

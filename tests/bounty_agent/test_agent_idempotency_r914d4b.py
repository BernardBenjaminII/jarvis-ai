from concurrent.futures import ThreadPoolExecutor

import pytest

from core.bounty_agent import engine as agent_engine
from core.bounty_agent.engine import (
    BountyAgent, BountyAgentError,
)
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine, "detect_platform", lambda: "kali"
    )

    auths = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="synthetic authorization",
        ttl=3600,
    )

    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    agent = BountyAgent(
        tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )

    return auths, auth, live, agent


def test_correlated_session_creation(environment):
    _, auth, live, agent = environment

    sid = agent.create(
        auth, "training.example",
        budget=5, operation_id="op-1",
    )

    report = agent.report(sid)

    assert report["session"]["operation_id"] == "op-1"
    assert report["mission"]["mission"]["operation_id"] == "op-1"


def test_repeated_creation_returns_same_session(environment):
    _, auth, live, agent = environment

    first = agent.create(
        auth, "training.example",
        budget=5, operation_id="op-1",
    )
    second = agent.create(
        auth, "training.example",
        budget=5, operation_id="op-1",
    )

    assert first == second

    with agent.db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

    assert count == 1


def test_recovery_after_live_mission_only(environment):
    _, auth, live, agent = environment

    mid = live.create(
        auth, budget=5, operation_id="op-crash"
    )

    sid = agent.create(
        auth, "training.example",
        budget=5, operation_id="op-crash",
    )

    assert agent.report(sid)["session"]["mission"] == mid


def test_concurrent_session_creation(environment):
    _, auth, live, agent = environment

    def create(_):
        return agent.create(
            auth, "training.example",
            budget=5, operation_id="op-concurrent",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        sessions = list(pool.map(create, range(16)))

    assert len(set(sessions)) == 1


def test_target_mismatch_rejected(environment):
    _, auth, live, agent = environment

    agent.create(
        auth, "training.example",
        budget=5, operation_id="op-target",
    )

    with pytest.raises(Exception):
        agent.create(
            auth, "different.example",
            budget=5, operation_id="op-target",
        )


def test_budget_mismatch_rejected(environment):
    _, auth, live, agent = environment

    agent.create(
        auth, "training.example",
        budget=5, operation_id="op-budget",
    )

    with pytest.raises(ValueError):
        agent.create(
            auth, "training.example",
            budget=10, operation_id="op-budget",
        )


def test_legacy_sessions_remain_distinct(environment):
    _, auth, live, agent = environment

    first = agent.create(
        auth, "training.example", budget=5
    )
    second = agent.create(
        auth, "training.example", budget=5
    )

    assert first != second


def test_restart_recovers_same_session(environment):
    auths, auth, live, agent = environment

    first = agent.create(
        auth, "training.example",
        budget=5, operation_id="op-restart",
    )

    reopened = BountyAgent(
        agent.path,
        authorization_store=auths,
        live_store=live,
    )

    second = reopened.create(
        auth, "training.example",
        budget=5, operation_id="op-restart",
    )

    assert first == second

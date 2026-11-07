"""R9.14B.2 — Real-store autonomous mission creation."""

import time

import pytest

import core.bounty_agent.engine as agent_engine
from core.bounty_agent.engine import BountyAgent
from core.bounty_agent.autonomy.authorization_bridge import (
    Candidate,
    AuthorizationBinding,
    select_authorized_candidate,
)
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine,
        "detect_platform",
        lambda: "kali",
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
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

    return auths, live, agent


def create_authorization(auths):
    return auths.create(
        program="jarvis-training",
        include=[
            "example.com",
            "*.example.com",
        ],
        exclude=[
            "private.example.com",
        ],
        capabilities=[
            "subfinder",
            "httpx",
        ],
        reviewer="test-reviewer",
        source_material="synthetic test authorization",
        ttl=3600,
    )


def select(auths, auth_id):
    return select_authorized_candidate(
        [
            Candidate(
                "unauthorized",
                "unauthorized.example",
                100,
            ),
            Candidate(
                "jarvis-training",
                "example.com",
                80,
            ),
        ],
        [
            AuthorizationBinding(
                authorization_id=auth_id,
                program="jarvis-training",
                target="example.com",
                reviewed=True,
                active=True,
            )
        ],
        scope_store=auths,
    )


def test_real_authorization_creates_mission(environment):
    auths, live, agent = environment
    auth_id = create_authorization(auths)

    selected = select(auths, auth_id)

    assert selected["status"] == (
        "authorized_candidate_selected"
    )
    assert selected["program"] == "jarvis-training"

    session_id = agent.create(
        selected["authorization_id"],
        selected["target"],
        budget=2,
    )

    report = agent.report(session_id)

    assert report["session"]["id"] == session_id
    assert report["session"]["program"] == (
        "jarvis-training"
    )
    assert report["session"]["state"] == "authorized"
    assert report["mission"]["mission"]["budget"] == 2
    assert report["mission"]["tasks"] == []

    assert report["human_gate"]["required_for"]


def test_revoked_authorization_is_rejected(environment):
    auths, _, _ = environment
    auth_id = create_authorization(auths)

    auths.revoke(auth_id, reason="test revocation")

    result = select(auths, auth_id)

    assert result["status"] == "no_authorized_candidate"


def test_expired_authorization_is_rejected(environment):
    auths, _, _ = environment
    auth_id = create_authorization(auths)

    with auths.db() as db:
        db.execute(
            "UPDATE authorizations SET expires=? WHERE id=?",
            (time.time() - 1, auth_id),
        )

    result = select(auths, auth_id)

    assert result["status"] == "no_authorized_candidate"


def test_tampered_scope_is_rejected(environment):
    auths, _, _ = environment
    auth_id = create_authorization(auths)

    with auths.db() as db:
        db.execute(
            "UPDATE authorizations SET scope_json=? WHERE id=?",
            ('{"program":"tampered"}', auth_id),
        )

    result = select(auths, auth_id)

    assert result["status"] == "no_authorized_candidate"


def test_excluded_host_is_rejected(environment):
    auths, _, _ = environment
    auth_id = create_authorization(auths)

    result = select_authorized_candidate(
        [
            Candidate(
                "jarvis-training",
                "private.example.com",
                90,
            )
        ],
        [
            AuthorizationBinding(
                authorization_id=auth_id,
                program="jarvis-training",
                target="private.example.com",
                reviewed=True,
                active=True,
            )
        ],
        scope_store=auths,
    )

    assert result["status"] == "no_authorized_candidate"

"""R9.14D.6B: offline durable approval integration tests."""

import sqlite3
import time

import pytest

from core.bounty_agent import engine as agent_engine
from core.bounty_agent.engine import BountyAgent
from core.bounty_agent.autonomy.approvals import (
    ApprovalDenied,
    ApprovalStore,
)
from core.bounty_agent.autonomy.coordinator import (
    CoordinationError,
    coordinate_mission,
)
from core.bounty_agent.autonomy.scheduler import MissionClaimStore
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine, "detect_platform", lambda: "kali"
    )

    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    authorization = auths.create(
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
    claims = MissionClaimStore(tmp_path / "claims.sqlite")
    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )

    return authorization, agent, claims, approvals


def request(environment):
    authorization, agent, claims, approvals = environment

    approval_id = approvals.issue(
        authorization=authorization,
        program="training",
        target="training.example",
        policy_digest="policy-v1",
        budget=5,
        reviewer="tester",
        ttl=600,
    )

    arguments = dict(
        claim_store=claims,
        agent=agent,
        authorization=authorization,
        program="training",
        target="training.example",
        policy_digest="policy-v1",
        budget=5,
        approval_store=approvals,
        approval_id=approval_id,
    )
    return arguments


def test_approved_mission_creation(environment):
    result = coordinate_mission(**request(environment))
    assert result.status == "mission_created"


def test_approved_retry_is_idempotent(environment):
    arguments = request(environment)

    first = coordinate_mission(**arguments)
    second = coordinate_mission(**arguments)

    assert second.status == "already_created"
    assert first.session_id == second.session_id
    assert first.mission_id == second.mission_id


def test_revoked_approval_blocks_retry(environment):
    arguments = request(environment)

    coordinate_mission(**arguments)
    arguments["approval_store"].revoke(
        arguments["approval_id"], "test"
    )

    with pytest.raises(ApprovalDenied):
        coordinate_mission(**arguments)


def test_approval_substitution_rejected(environment):
    arguments = request(environment)
    coordinate_mission(**arguments)

    approvals = arguments["approval_store"]
    replacement = approvals.issue(
        authorization=arguments["authorization"],
        program=arguments["program"],
        target=arguments["target"],
        policy_digest=arguments["policy_digest"],
        budget=arguments["budget"],
        reviewer="different-reviewer",
        ttl=600,
    )

    arguments["approval_id"] = replacement

    with pytest.raises(sqlite3.IntegrityError):
        coordinate_mission(**arguments)


def test_missing_approval_id_rejected(environment):
    arguments = request(environment)
    arguments["approval_id"] = None

    with pytest.raises(CoordinationError):
        coordinate_mission(**arguments)


def test_callback_and_approval_cannot_mix(environment):
    arguments = request(environment)
    arguments["verify_approval"] = lambda **kwargs: True

    with pytest.raises(TypeError):
        coordinate_mission(**arguments)

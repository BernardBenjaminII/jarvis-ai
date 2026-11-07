from core.bounty_agent.autonomy.approvals import ApprovalStore
from core.bounty_agent.autonomy.scheduler import MissionClaimStore
from types import SimpleNamespace

import pytest

import core.bounty_agent.engine as agent_engine
import core.bounty_agent.autonomy.catalog_controller as controller
from core.bounty_agent.engine import BountyAgent
from core.bounty_authorization import AuthorizationStore
from core.bounty_live import LiveMissionStore


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        agent_engine, "detect_platform", lambda: "kali"
    )

    auths = AuthorizationStore(tmp_path / "auth.sqlite")
    live = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )
    agent = BountyAgent(
        tmp_path / "agent.sqlite",
        authorization_store=auths,
        live_store=live,
    )
    return auths, agent


def authorize(auths, program="training"):
    return auths.create(
        program=program,
        include=["training.example"],
        capabilities=["subfinder", "httpx"],
        reviewer="test-reviewer",
        source_material="synthetic reviewed policy",
        ttl=3600,
    )


def ranked(handle="training", score=80, blockers=None):
    return {
        "opportunities": [{
            "handle": handle,
            "submission_state": "open",
            "policy_signals": {
                "automation_policy": "conditionally_permitted",
            },
            "lane": "POLICY_REVIEW",
            "blockers": blockers or [],
            "automation_viability_score": score,
            "manual_hunt_viability_score": 50,
        }]
    }


def test_creates_real_mission(environment, monkeypatch, tmp_path):
    auths, agent = environment
    auth_id = authorize(auths)

    monkeypatch.setattr(
        controller, "rank_catalog",
        lambda catalog: ranked(),
    )

    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )
    claims = MissionClaimStore(tmp_path / "claims.sqlite")
    approval_id = approvals.issue(
        authorization=auth_id,
        program="training",
        target="training.example",
        policy_digest="synthetic-policy-v1",
        budget=2,
        reviewer="test-reviewer",
        ttl=600,
    )

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        claim_store=claims,
        approval_store=approvals,
        approval_id=approval_id,
        policy_digest="synthetic-policy-v1",
        budget=2,
    )

    assert result.status == "mission_created"
    assert result.program == "training"
    assert result.session_id
    assert result.mission_id

    report = agent.report(result.session_id)
    assert report["mission"]["tasks"] == []


def test_no_approval_no_mission(environment, monkeypatch):
    auths, agent = environment
    authorize(auths)

    monkeypatch.setattr(
        controller, "rank_catalog",
        lambda catalog: ranked(),
    )

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
    )

    assert result.status == "durable_approval_required"
    assert agent.list_sessions() == []


def test_blocked_program_rejected(environment, monkeypatch):
    auths, agent = environment
    auth_id = authorize(auths)

    monkeypatch.setattr(
        controller, "rank_catalog",
        lambda catalog: ranked(blockers=["policy review required"]),
    )

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        autonomous_approval_ids=[auth_id],
    )

    assert result.status == "no_authorized_candidate"


def test_revoked_authorization_rejected(environment, monkeypatch):
    auths, agent = environment
    auth_id = authorize(auths)
    auths.revoke(auth_id)

    monkeypatch.setattr(
        controller, "rank_catalog",
        lambda catalog: ranked(),
    )

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        autonomous_approval_ids=[auth_id],
    )

    assert result.status == "no_authorized_candidate"


def test_empty_catalog(environment, monkeypatch):
    auths, agent = environment
    auth_id = authorize(auths)

    monkeypatch.setattr(
        controller, "rank_catalog",
        lambda catalog: {"opportunities": []},
    )

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        autonomous_approval_ids=[auth_id],
    )

    assert result.status == "no_authorized_candidate"

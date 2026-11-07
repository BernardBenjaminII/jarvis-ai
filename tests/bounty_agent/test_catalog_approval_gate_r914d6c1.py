"""R9.14D.6C.1: catalog must fail closed."""

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
    auth = auths.create(
        program="training",
        include=["training.example"],
        reviewer="tester",
        source_material="synthetic policy",
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

    monkeypatch.setattr(
        controller,
        "rank_catalog",
        lambda catalog: {
            "opportunities": [{
                "handle": "training",
                "submission_state": "open",
                "policy_signals": {
                    "automation_policy": "explicitly_permitted",
                },
                "lane": "POLICY_REVIEW",
                "blockers": [],
                "automation_viability_score": 80,
                "manual_hunt_viability_score": 50,
            }]
        },
    )

    return auths, auth, agent


def test_legacy_authorization_id_cannot_create(environment):
    auths, auth, agent = environment

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        autonomous_approval_ids=[auth],
    )

    assert result.status == "durable_approval_required"
    assert agent.list_sessions() == []


def test_missing_durable_approval_cannot_create(environment):
    auths, _, agent = environment

    result = controller.plan_catalog_mission(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
    )

    assert result.status == "durable_approval_required"
    assert agent.list_sessions() == []


def approved_request(environment, tmp_path):
    from core.bounty_agent.autonomy.approvals import ApprovalStore
    from core.bounty_agent.autonomy.scheduler import MissionClaimStore

    auths, auth, agent = environment
    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )
    claims = MissionClaimStore(tmp_path / "claims.sqlite")

    approval_id = approvals.issue(
        authorization=auth,
        program="training",
        target="training.example",
        policy_digest="synthetic-policy-v1",
        budget=2,
        reviewer="test-reviewer",
        ttl=600,
    )

    return dict(
        catalog=object(),
        authorization_store=auths,
        agent=agent,
        claim_store=claims,
        approval_store=approvals,
        approval_id=approval_id,
        policy_digest="synthetic-policy-v1",
        budget=2,
    )


def test_durable_approval_creates_mission(
    environment, tmp_path
):
    arguments = approved_request(environment, tmp_path)

    result = controller.plan_catalog_mission(**arguments)

    assert result.status == "mission_created"
    assert result.session_id
    assert result.mission_id
    assert result.target == "training.example"

    report = arguments["agent"].report(result.session_id)
    assert report["mission"]["tasks"] == []


def test_durable_approval_retry_is_idempotent(
    environment, tmp_path
):
    arguments = approved_request(environment, tmp_path)

    first = controller.plan_catalog_mission(**arguments)
    second = controller.plan_catalog_mission(**arguments)

    assert first.status == "mission_created"
    assert second.status == "already_created"
    assert first.session_id == second.session_id
    assert first.mission_id == second.mission_id


def test_revoked_approval_blocks_catalog_retry(
    environment, tmp_path
):
    from core.bounty_agent.autonomy.approvals import ApprovalDenied

    arguments = approved_request(environment, tmp_path)
    controller.plan_catalog_mission(**arguments)

    arguments["approval_store"].revoke(
        arguments["approval_id"], "test revocation"
    )

    with pytest.raises(ApprovalDenied):
        controller.plan_catalog_mission(**arguments)

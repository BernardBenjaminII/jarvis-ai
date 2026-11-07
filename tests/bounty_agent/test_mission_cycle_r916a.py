
"""R9.16A: offline mission lifecycle integration tests."""

import json

import pytest

from core.bounty_agent import engine as agent_engine
from core.bounty_agent.engine import BountyAgent
from core.bounty_agent.autonomy.approvals import (
    ApprovalDenied,
    ApprovalStore,
)
from core.bounty_agent.autonomy.mission_cycle import (
    MissionCycleError,
    run_offline_cycle,
)
from core.bounty_agent.autonomy.proposals import ProposalStore
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

    proposals = ProposalStore(tmp_path / "proposals.sqlite")
    proposal = proposals.create(
        program="training",
        target="training.example",
        authorization_id=authorization,
        policy_digest="policy-v1",
        budget=2,
    )

    approvals = ApprovalStore(
        tmp_path / "approvals.sqlite",
        authorization_store=auths,
    )
    approval_id = approvals.issue(
        authorization=authorization,
        program="training",
        target="training.example",
        policy_digest="policy-v1",
        budget=2,
        reviewer="tester",
    )

    return {
        "proposal_store": proposals,
        "approval_store": approvals,
        "claim_store": MissionClaimStore(
            tmp_path / "claims.sqlite"
        ),
        "agent": agent,
        "proposal_id": proposal["id"],
        "approval_id": approval_id,
        "output_dir": tmp_path / "reports",
    }


def test_complete_offline_mission(environment):
    result = run_offline_cycle(**environment)

    assert result["status"] == "awaiting_human_review"
    assert result["simulation_only"] is True

    with open(result["report_path"], encoding="utf-8") as f:
        report = json.load(f)

    assert report["simulation_only"] is True
    assert report["validated_vulnerabilities"] == 0
    assert report["submission_authorized"] is False
    assert report["observations"][0]["target"] == (
        "training.example"
    )
    assert report["mission_id"] == result["mission_id"]


def test_retry_is_idempotent(environment):
    first = run_offline_cycle(**environment)
    second = run_offline_cycle(**environment)

    assert first["session_id"] == second["session_id"]
    assert first["mission_id"] == second["mission_id"]
    assert first["report_path"] == second["report_path"]


def test_revoked_approval_rejected(environment):
    run_offline_cycle(**environment)

    environment["approval_store"].revoke(
        environment["approval_id"], "test"
    )

    with pytest.raises(ApprovalDenied):
        run_offline_cycle(**environment)


def test_cancelled_proposal_rejected(environment):
    environment["proposal_store"].cancel(
        environment["proposal_id"]
    )

    with pytest.raises(MissionCycleError):
        run_offline_cycle(**environment)


def test_missing_proposal_rejected(environment):
    environment["proposal_id"] = "missing"

    with pytest.raises(MissionCycleError):
        run_offline_cycle(**environment)


def test_mission_artifact_contains_recon_plan(environment):
    result = run_offline_cycle(**environment)

    with open(result["report_path"], encoding="utf-8") as f:
        artifact = json.load(f)

    plan = artifact["recon_plan"]

    assert plan["schema"] == "jarvis.bounty.recon_plan.r916b"
    assert plan["target"] == "training.example"
    assert plan["authorization_id"] == (
        artifact["authorization_id"]
    )
    assert plan["budget"] == 2
    assert plan["execution_started"] is False
    assert plan["automatic_execution_allowed"] is False
    assert plan["planned_cost"] <= plan["budget"]


def test_mission_artifact_contains_recon_plan(environment):
    result = run_offline_cycle(**environment)

    with open(result["report_path"], encoding="utf-8") as f:
        artifact = json.load(f)

    plan = artifact["recon_plan"]

    assert plan["schema"] == "jarvis.bounty.recon_plan.r916b"
    assert plan["target"] == "training.example"
    assert plan["authorization_id"] == artifact["authorization_id"]
    assert plan["budget"] == 2
    assert plan["execution_started"] is False
    assert plan["automatic_execution_allowed"] is False
    assert plan["planned_cost"] <= plan["budget"]


def test_mission_artifact_contains_strategy(environment):
    result = run_offline_cycle(**environment)

    with open(result["report_path"], encoding="utf-8") as f:
        artifact = json.load(f)

    strategy = artifact["investigation_strategy"]

    assert strategy["schema"] == (
        "jarvis.bounty.investigation_strategy.r916c"
    )
    assert strategy["target"] == "training.example"
    assert strategy["authorization_id"] == (
        artifact["authorization_id"]
    )
    assert strategy["recommended_next_action"] == "human_review"
    assert strategy["automatic_execution_allowed"] is False
    assert strategy["report_submission_allowed"] is False


def test_mission_artifact_contains_opportunity_scoring(environment):
    result = run_offline_cycle(**environment)

    with open(result["report_path"], encoding="utf-8") as f:
        artifact = json.load(f)

    scoring = artifact["opportunity_scoring"]
    plan = artifact["recon_plan"]

    assert scoring["schema"] == (
        "jarvis.bounty.opportunity_scoring.r916c3"
    )
    assert scoring["target"] == "training.example"
    assert scoring["automatic_execution_allowed"] is False
    assert scoring["report_submission_allowed"] is False

    selected = {
        task["capability"] for task in plan["tasks"]
    }

    for item in scoring["ranked_opportunities"]:
        if item["eligible"]:
            assert item["required_capability"] in selected
        assert item["vulnerability_confidence"] == 0
        assert item["execution_allowed"] is False

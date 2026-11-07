"""R9.15A.2 offline orchestration tests."""

import pytest

from core.bounty_agent.autonomy import orchestrator
from core.bounty_agent.autonomy.catalog_controller import (
    MissionSelection,
)


def test_proposal_contains_selected_candidate(monkeypatch):
    def fake_plan(**kwargs):
        assert kwargs["approval_id"] if "approval_id" in kwargs else True

        return MissionSelection(
            status="durable_approval_required",
            program="synthetic-program",
            target="target.example",
            authorization_id="synthetic-auth",
        )

    monkeypatch.setattr(
        orchestrator,
        "plan_catalog_mission",
        fake_plan,
    )

    proposal = orchestrator.propose_mission(
        catalog={},
        authorization_store=object(),
        policy_digest="synthetic-policy-digest",
        budget=2,
    )

    assert proposal.status == "awaiting_human_approval"
    assert proposal.program == "synthetic-program"
    assert proposal.target == "target.example"
    assert proposal.authorization_id == "synthetic-auth"
    assert proposal.budget == 2


def test_no_candidate(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "plan_catalog_mission",
        lambda **kwargs: MissionSelection(
            status="no_authorized_candidate"
        ),
    )

    proposal = orchestrator.propose_mission(
        catalog={},
        authorization_store=object(),
        policy_digest="synthetic-policy-digest",
    )

    assert proposal.status == "no_authorized_candidate"


@pytest.mark.parametrize("budget", [0, 11, True, -1])
def test_invalid_budget_rejected(budget):
    with pytest.raises(ValueError):
        orchestrator.propose_mission(
            catalog={},
            authorization_store=object(),
            policy_digest="synthetic-policy-digest",
            budget=budget,
        )


def test_missing_policy_rejected():
    with pytest.raises(ValueError):
        orchestrator.propose_mission(
            catalog={},
            authorization_store=object(),
            policy_digest="",
        )

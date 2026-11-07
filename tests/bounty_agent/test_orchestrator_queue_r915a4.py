"""R9.15A.4 orchestrator proposal queue tests."""

from core.bounty_agent.autonomy import orchestrator
from core.bounty_agent.autonomy.catalog_controller import (
    MissionSelection,
)
from core.bounty_agent.autonomy.proposals import ProposalStore


def test_autonomous_proposal_is_persisted(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        orchestrator,
        "plan_catalog_mission",
        lambda **kwargs: MissionSelection(
            status="durable_approval_required",
            program="synthetic-program",
            target="target.example",
            authorization_id="synthetic-auth",
        ),
    )

    store = ProposalStore(tmp_path / "proposals.sqlite")

    result = orchestrator.queue_mission_proposal(
        catalog={},
        authorization_store=object(),
        proposal_store=store,
        policy_digest="synthetic-policy",
    )

    assert result["status"] == "proposal_queued"
    assert result["proposal"]["status"] == "pending"
    assert len(store.pending()) == 1


def test_repeated_cycle_does_not_duplicate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        orchestrator,
        "plan_catalog_mission",
        lambda **kwargs: MissionSelection(
            status="durable_approval_required",
            program="synthetic-program",
            target="target.example",
            authorization_id="synthetic-auth",
        ),
    )

    store = ProposalStore(tmp_path / "proposals.sqlite")

    def run():
        return orchestrator.queue_mission_proposal(
            catalog={},
            authorization_store=object(),
            proposal_store=store,
            policy_digest="synthetic-policy",
        )

    first = run()
    second = run()

    assert (
        first["proposal"]["id"]
        == second["proposal"]["id"]
    )
    assert len(store.pending()) == 1


def test_no_candidate_creates_no_proposal(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        orchestrator,
        "plan_catalog_mission",
        lambda **kwargs: MissionSelection(
            status="no_authorized_candidate"
        ),
    )

    store = ProposalStore(tmp_path / "proposals.sqlite")

    result = orchestrator.queue_mission_proposal(
        catalog={},
        authorization_store=object(),
        proposal_store=store,
        policy_digest="synthetic-policy",
    )

    assert result["status"] == "no_authorized_candidate"
    assert store.pending() == []

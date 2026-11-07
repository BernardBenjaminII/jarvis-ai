"""R9.15A.3 persistent proposal tests."""

import pytest

from core.bounty_agent.autonomy.proposals import (
    ProposalError,
    ProposalStore,
)


def create(store, **overrides):
    values = dict(
        program="synthetic-program",
        target="target.example",
        authorization_id="synthetic-auth",
        policy_digest="synthetic-policy",
        budget=2,
    )
    values.update(overrides)
    return store.create(**values)


def test_proposal_persists_across_reopen(tmp_path):
    path = tmp_path / "proposals.sqlite"
    store = ProposalStore(path)
    proposal = create(store)

    reopened = ProposalStore(path)

    assert reopened.get(proposal["id"]) == proposal


def test_duplicate_pending_is_idempotent(tmp_path):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    first = create(store)
    second = create(store)

    assert first["id"] == second["id"]
    assert len(store.pending()) == 1


def test_different_target_creates_new_proposal(tmp_path):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    first = create(store)
    second = create(store, target="other.example")

    assert first["id"] != second["id"]


def test_cancel_prevents_reuse(tmp_path):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    first = create(store)
    store.cancel(first["id"])

    assert store.get(first["id"])["status"] == "cancelled"
    assert store.pending() == []

    second = create(store)
    assert second["id"] != first["id"]


def test_double_cancel_rejected(tmp_path):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    proposal = create(store)
    store.cancel(proposal["id"])

    with pytest.raises(ProposalError):
        store.cancel(proposal["id"])


@pytest.mark.parametrize("budget", [0, 11, True])
def test_invalid_budget(tmp_path, budget):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    with pytest.raises(ProposalError):
        create(store, budget=budget)


def test_invalid_ttl(tmp_path):
    store = ProposalStore(tmp_path / "proposals.sqlite")

    with pytest.raises(ProposalError):
        create(store, ttl=0)

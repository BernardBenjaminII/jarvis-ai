"""R9.22B1 offline opportunity queue regression."""

import copy

import pytest

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
    build_imported_opportunity_queue,
)


def records(tmp_path):
    store = ProgramScopeStore(tmp_path / "policies.sqlite3")

    sources = [
        (
            "hackerone",
            "https://hackerone.com/training",
        ),
        (
            "bugcrowd",
            "https://bugcrowd.com/engagements/training",
        ),
        (
            "intigriti",
            "https://app.intigriti.com/programs/training",
        ),
    ]

    result = []

    for platform, url in sources:
        draft = create_scope_draft(
            platform=platform,
            program=f"Synthetic {platform}",
            policy_url=url,
            in_scope=[f"api.{platform}.example"],
            out_of_scope=[],
            restrictions=["No automated scanning"],
        )

        identity = store.import_draft(draft)
        result.append(store.get_draft(identity))

    return result


def test_three_platforms_normalized(tmp_path):
    result = build_imported_opportunity_queue(records(tmp_path))

    assert result["opportunity_count"] == 3
    assert {
        item["platform"]
        for item in result["opportunities"]
    } == {"hackerone", "bugcrowd", "intigriti"}


def test_imports_never_grant_authorization(tmp_path):
    result = build_imported_opportunity_queue(records(tmp_path))

    assert result["automatic_execution_allowed"] is False
    assert result["network_requests"] == 0

    for item in result["opportunities"]:
        assert item["policy_review_status"] == "unverified"
        assert item["program_eligibility"] == "unknown"
        assert item["reward_status"] == "unverified"
        assert item["testing_authorized"] is False
        assert item["execution_enabled"] is False
        assert item["automatic_execution_ready"] is False
        assert item["submission_authorized"] is False


def test_deterministic_ordering(tmp_path):
    items = records(tmp_path)

    first = build_imported_opportunity_queue(items)
    second = build_imported_opportunity_queue(
        list(reversed(items))
    )

    assert first == second


def test_duplicates_collapsed(tmp_path):
    items = records(tmp_path)

    result = build_imported_opportunity_queue(
        items + [items[0]]
    )

    assert result["opportunity_count"] == 3


def test_tampered_policy_rejected(tmp_path):
    items = records(tmp_path)
    changed = copy.deepcopy(items)

    changed[0]["draft"]["program"] = "Forged Program"

    with pytest.raises(ValueError):
        build_imported_opportunity_queue(changed)


def test_forged_review_status_rejected(tmp_path):
    items = records(tmp_path)
    changed = copy.deepcopy(items)

    changed[0]["review_status"] = "approved"

    with pytest.raises(OpportunityQueueError):
        build_imported_opportunity_queue(changed)


def test_forged_execution_permission_rejected(tmp_path):
    items = records(tmp_path)
    changed = copy.deepcopy(items)

    changed[0]["execution_authorized"] = True

    with pytest.raises(OpportunityQueueError):
        build_imported_opportunity_queue(changed)


def test_empty_queue():
    result = build_imported_opportunity_queue([])

    assert result["opportunity_count"] == 0
    assert result["opportunities"] == []

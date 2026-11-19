"""R9.22B2 offline unified opportunity queue regression."""

import json
import time

import pytest

from core.bounty_catalog.store import Catalog
from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
)
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)
from core.bounty_agent.autonomy.program_opportunities_r922b2 import (
    build_unified_opportunity_queue,
)


def make_catalog(tmp_path, *, status="complete",
                 source="hackerone-api", submission="open"):
    catalog = Catalog(tmp_path / "catalog.sqlite3")

    raw = json.dumps({
        "data": [{
            "type": "program",
            "attributes": {
                "handle": "jarvis-training",
                "name": "JARVIS Synthetic Training",
                "offers_bounties": True,
                "submission_state": submission,
                "state": "public_mode",
                "open_scope": True,
                "policy": (
                    "Synthetic training information only. "
                    "No real-world testing authorization."
                ),
            },
        }],
        "links": {},
    }).encode()

    observed = time.time()

    catalog.save(
        source,
        observed,
        [(1, raw, observed)],
        status,
    )

    return catalog


def manual_records(tmp_path):
    store = ProgramScopeStore(tmp_path / "imports.sqlite3")

    draft = create_scope_draft(
        platform="bugcrowd",
        program="Synthetic Bugcrowd Training",
        policy_url="https://bugcrowd.com/engagements/training",
        in_scope=["api.training.example"],
        out_of_scope=[],
        restrictions=["No automated scanning"],
    )

    identity = store.import_draft(draft)
    return [store.get_draft(identity)]


def evaluate(catalog, records, **kwargs):
    return build_unified_opportunity_queue(
        catalog,
        records,
        **kwargs,
    )


def test_fresh_catalog_and_manual_imports(tmp_path):
    catalog = make_catalog(tmp_path)
    result = evaluate(
        catalog,
        manual_records(tmp_path),
        now=time.time() + 1,
    )

    assert result["opportunity_count"] == 2
    assert result["sources"]["hackerone_catalog"]["status"] == "fresh"

    assert {
        item["source"]
        for item in result["opportunities"]
    } == {
        "hackerone_api_snapshot",
        "manual_policy_import",
    }


def test_no_permission_granted(tmp_path):
    result = evaluate(
        make_catalog(tmp_path),
        manual_records(tmp_path),
        now=time.time() + 1,
    )

    assert result["network_requests"] == 0
    assert result["automatic_execution_allowed"] is False
    assert result["testing_authorized"] is False
    assert result["submission_authorized"] is False

    for item in result["opportunities"]:
        assert item["testing_authorized"] is False
        assert item["execution_enabled"] is False
        assert item["automatic_execution_ready"] is False
        assert item["submission_authorized"] is False
        assert item["program_eligibility"] == "unknown"


def test_missing_catalog_preserves_manual_imports(tmp_path):
    catalog = Catalog(tmp_path / "empty.sqlite3")

    result = evaluate(catalog, manual_records(tmp_path))

    assert result["sources"]["hackerone_catalog"]["status"] == "missing"
    assert result["opportunity_count"] == 1


def test_incomplete_catalog_is_not_ranked(tmp_path, monkeypatch):
    catalog = make_catalog(tmp_path, status="limited")

    def forbidden(_):
        pytest.fail("Incomplete catalog must not be ranked")

    monkeypatch.setattr(
        "core.bounty_agent.autonomy."
        "program_opportunities_r922b2.rank_catalog",
        forbidden,
    )

    result = evaluate(catalog, manual_records(tmp_path))

    assert result["sources"]["hackerone_catalog"]["status"] == "incomplete"
    assert result["opportunity_count"] == 1


def test_stale_catalog_is_not_ranked(tmp_path):
    catalog = make_catalog(tmp_path)

    with catalog.connect() as db:
        db.execute(
            "UPDATE runs SET finished = ? WHERE source = ?",
            (time.time() - 172800, "hackerone-api"),
        )

    result = evaluate(catalog, [], now=time.time())

    assert result["sources"]["hackerone_catalog"]["status"] == "stale"
    assert result["opportunity_count"] == 0


def test_future_dated_catalog_is_not_ranked(tmp_path):
    catalog = make_catalog(tmp_path)

    with catalog.connect() as db:
        db.execute(
            "UPDATE runs SET finished = ? WHERE source = ?",
            (time.time() + 3600, "hackerone-api"),
        )

    result = evaluate(catalog, [], now=time.time())

    assert result["sources"]["hackerone_catalog"]["status"] == "future_dated"
    assert result["opportunity_count"] == 0


def test_manual_catalog_cannot_impersonate_api(tmp_path):
    catalog = make_catalog(
        tmp_path,
        source="hackerone-import",
    )

    result = evaluate(catalog, [])

    assert result["sources"]["hackerone_catalog"]["status"] == "missing"
    assert result["opportunity_count"] == 0


def test_paused_program_is_not_recommended(tmp_path):
    catalog = make_catalog(tmp_path, submission="paused")

    result = evaluate(catalog, [], now=time.time() + 1)
    item = result["opportunities"][0]

    assert item["source_lane"] == "SKIP"
    assert item["recommendation"] == "skip_until_program_state_changes"
    assert item["testing_authorized"] is False


def test_unsafe_ranker_output_rejected(tmp_path, monkeypatch):
    catalog = make_catalog(tmp_path)

    def unsafe(_):
        return {
            "source": "stored_hackerone_catalog",
            "network_requests": 0,
            "testing_authorized": True,
            "execution_enabled": False,
            "payout_values_authoritative": False,
            "program_count": 0,
            "opportunities": [],
        }

    monkeypatch.setattr(
        "core.bounty_agent.autonomy."
        "program_opportunities_r922b2.rank_catalog",
        unsafe,
    )

    with pytest.raises(OpportunityQueueError):
        evaluate(catalog, [], now=time.time() + 1)


def test_invalid_snapshot_age_rejected(tmp_path):
    catalog = Catalog(tmp_path / "empty.sqlite3")

    with pytest.raises(OpportunityQueueError):
        evaluate(catalog, [], max_age_seconds=0)

"""R9.22C1 read-only capability ranking regression."""

import copy
import json
import time

import pytest

from core.capabilities.kali_workstation import TOOLS
from core.bounty_catalog.store import Catalog
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
)
from core.bounty_agent.autonomy.program_opportunities_r922b2 import (
    build_unified_opportunity_queue,
)
from core.bounty_agent.autonomy.program_capability_fit_r922c1 import (
    rank_opportunity_reviews,
)


def inventory(missing=()):
    installed = set(TOOLS) - set(missing)

    return {
        "state": (
            "ready" if len(installed) == len(TOOLS)
            else "degraded"
        ),
        "mode": "inventory_only",
        "execution_authorized": False,
        "tool_count": len(TOOLS),
        "installed_count": len(installed),
        "tools": {
            name: {
                "installed": name in installed,
                "path": (
                    f"/usr/bin/{name}"
                    if name in installed else None
                ),
            }
            for name in TOOLS
        },
        "arsenal": {"state": "unknown"},
    }


def opportunity(handle="training", lane="POLICY_REVIEW",
                score=60):
    return {
        "source": "hackerone_api_snapshot",
        "platform": "hackerone",
        "program": f"Program {handle}",
        "handle": handle,
        "policy_url": f"https://hackerone.com/{handle}",
        "source_lane": lane,
        "manual_hunt_viability_score": score,
        "payout_values_authoritative": False,
        "program_eligibility": "unknown",
        "policy_review_status": "unverified",
        "testing_authorized": False,
        "execution_enabled": False,
        "automatic_execution_ready": False,
        "submission_authorized": False,
    }


def manual():
    return {
        "source": "manual_policy_import",
        "platform": "bugcrowd",
        "program": "Manual Training Program",
        "draft_id": "synthetic-draft",
        "policy_url": "https://bugcrowd.com/engagements/training",
        "program_eligibility": "unknown",
        "policy_review_status": "unverified",
        "testing_authorized": False,
        "execution_enabled": False,
        "automatic_execution_ready": False,
        "submission_authorized": False,
    }


def queue(items):
    return {
        "schema": "jarvis.bounty.program_opportunities.r922b2",
        "mode": "offline_unified_opportunity_queue",
        "network_requests": 0,
        "testing_authorized": False,
        "automatic_execution_allowed": False,
        "submission_authorized": False,
        "opportunity_count": len(items),
        "sources": {
            "hackerone_catalog": {"status": "fresh"},
            "manual_policy_import": {"status": "available"},
        },
        "opportunities": items,
    }


def test_full_workstation_readiness():
    result = rank_opportunity_reviews(
        queue([opportunity()]),
        inventory(),
    )

    assert result["workstation"]["coverage_percent"] == 100
    assert result["workstation"]["missing_tools"] == []
    assert result["opportunity_count"] == 1


def test_missing_tools_reported_without_execution():
    result = rank_opportunity_reviews(
        queue([opportunity()]),
        inventory(missing=("nuclei", "masscan")),
    )

    workstation = result["workstation"]

    assert workstation["coverage_percent"] == 75
    assert set(workstation["missing_tools"]) == {
        "nuclei", "masscan"
    }
    assert (
        workstation["categories"]["template_analysis"]["status"]
        == "unavailable"
    )
    assert (
        workstation["categories"]["network_inventory"]["status"]
        == "partial"
    )
    assert result["automatic_execution_allowed"] is False


def test_review_order_respects_existing_lanes():
    result = rank_opportunity_reviews(
        queue([
            opportunity("paused", "SKIP", 100),
            manual(),
            opportunity("active", "POLICY_REVIEW", 55),
        ]),
        inventory(),
    )

    assert [
        item["source_identifier"]
        for item in result["opportunities"]
    ] == ["active", "synthetic-draft", "paused"]


def test_no_program_specific_fit_invented():
    result = rank_opportunity_reviews(
        queue([opportunity()]),
        inventory(),
    )

    item = result["opportunities"][0]

    assert item["program_specific_capability_fit"] is None
    assert item["human_review_required"] is True
    assert item["testing_authorized"] is False
    assert item["execution_enabled"] is False
    assert item["automatic_execution_ready"] is False
    assert item["submission_authorized"] is False
    assert result["mission_creation_allowed"] is False
    assert result["network_requests"] == 0


def test_deterministic_and_does_not_mutate_inputs():
    original = queue([
        manual(),
        opportunity("zeta", score=20),
        opportunity("alpha", score=90),
    ])

    saved = copy.deepcopy(original)

    a = rank_opportunity_reviews(original, inventory())
    b = rank_opportunity_reviews(
        queue(list(reversed(original["opportunities"]))),
        inventory(),
    )

    assert a == b
    assert original == saved


def test_forged_program_authorization_rejected():
    bad = queue([opportunity()])
    bad["opportunities"][0]["execution_enabled"] = True

    with pytest.raises(OpportunityQueueError):
        rank_opportunity_reviews(bad, inventory())


def test_forged_workstation_authorization_rejected():
    bad = inventory()
    bad["execution_authorized"] = True

    with pytest.raises(OpportunityQueueError):
        rank_opportunity_reviews(
            queue([opportunity()]), bad
        )


def test_inconsistent_inventory_rejected():
    bad = inventory()
    bad["installed_count"] = 999

    with pytest.raises(OpportunityQueueError):
        rank_opportunity_reviews(
            queue([opportunity()]), bad
        )


def test_stale_catalog_records_rejected():
    bad = queue([opportunity()])
    bad["sources"]["hackerone_catalog"]["status"] = "stale"

    with pytest.raises(OpportunityQueueError):
        rank_opportunity_reviews(bad, inventory())


def test_duplicate_program_identity_rejected():
    with pytest.raises(OpportunityQueueError):
        rank_opportunity_reviews(
            queue([opportunity(), opportunity()]),
            inventory(),
        )


def test_real_b2_catalog_contract(tmp_path):
    catalog = Catalog(tmp_path / "catalog.sqlite3")

    raw = json.dumps({
        "data": [{
            "type": "program",
            "attributes": {
                "handle": "jarvis-training",
                "name": "JARVIS Training",
                "offers_bounties": True,
                "submission_state": "open",
                "state": "public_mode",
                "policy": "Synthetic training record only.",
            },
        }],
        "links": {},
    }).encode()

    observed = time.time()

    catalog.save(
        "hackerone-api",
        observed,
        [(1, raw, observed)],
        "complete",
    )

    unified = build_unified_opportunity_queue(
        catalog,
        [],
        now=time.time() + 1,
    )

    result = rank_opportunity_reviews(unified, inventory())

    assert result["opportunity_count"] == 1
    assert (
        result["opportunities"][0]["source_identifier"]
        == "jarvis-training"
    )
    assert result["automatic_execution_allowed"] is False

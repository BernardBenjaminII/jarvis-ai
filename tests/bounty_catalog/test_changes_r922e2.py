import json
import sqlite3
import time

import pytest

from core.bounty_catalog.store import Catalog
from core.bounty_catalog.changes_r922e2 import (
    SnapshotError,
    compare_catalog,
)


def make_catalog(tmp_path):
    return Catalog(tmp_path / "catalog.sqlite")


def save(catalog, programs, status="complete", more=False):
    items = [
        {
            "type": "program",
            "attributes": {
                "handle": handle,
                "name": attrs.get("name", handle),
                "offers_bounties": attrs.get("paid", True),
                "submission_state": attrs.get("state", "open"),
                "state": "public_mode",
                "policy": attrs.get("policy", "Synthetic policy"),
                "updated_at": attrs.get("updated_at"),
            },
        }
        for handle, attrs in programs.items()
    ]

    links = {}
    if more:
        links["next"] = (
            "https://api.hackerone.com/v1/hackers/programs"
            "?page%5Bnumber%5D=2&page%5Bsize%5D=100"
        )

    raw = json.dumps({
        "data": items,
        "links": links,
    }).encode()

    now = time.time()

    return catalog.save(
        "hackerone-api",
        now,
        [(1, raw, now)],
        status,
    )


def test_missing_catalog_never_created(tmp_path):
    path = tmp_path / "missing.sqlite"
    result = compare_catalog(path)

    assert result["status"] == "catalog_missing"
    assert result["event_count"] == 0
    assert not path.exists()


def test_first_complete_run_establishes_baseline(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}, "beta": {}})

    before = catalog.path.read_bytes()
    result = compare_catalog(catalog.path)

    assert result["status"] == "baseline_established"
    assert result["current_program_count"] == 2
    assert result["event_count"] == 0
    assert result["alerts_issued"] == 0
    assert result["network_requests"] == 0
    assert result["testing_authorized"] is False
    assert catalog.path.read_bytes() == before


def test_incomplete_runs_do_not_establish_baseline(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}}, status="limited", more=True)

    result = compare_catalog(catalog.path)

    assert result["status"] == "blocked_latest_run_incomplete"
    assert result["events"] == []


def test_latest_incomplete_run_blocks_changes(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}})
    save(catalog, {"alpha": {}, "beta": {}},
         status="limited", more=True)

    result = compare_catalog(catalog.path)

    assert result["status"] == "blocked_latest_run_incomplete"
    assert result["event_count"] == 0


def test_additions_and_removals(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}, "beta": {}})
    save(catalog, {"beta": {}, "gamma": {}})

    result = compare_catalog(catalog.path)

    assert result["status"] == "compared"
    assert result["change_counts"]["new_listing"] == 1
    assert result["change_counts"]["no_longer_listed"] == 1
    assert result["event_count"] == 2

    assert {
        (event["handle"], event["type"])
        for event in result["events"]
    } == {
        ("alpha", "no_longer_listed"),
        ("gamma", "new_listing"),
    }


def test_material_status_and_policy_changes(tmp_path):
    catalog = make_catalog(tmp_path)

    save(catalog, {
        "alpha": {
            "paid": False,
            "state": "closed",
            "policy": "Old synthetic policy",
        }
    })

    save(catalog, {
        "alpha": {
            "paid": True,
            "state": "open",
            "policy": "New synthetic policy",
        }
    })

    result = compare_catalog(catalog.path)

    assert result["event_count"] == 1

    event = result["events"][0]
    assert event["type"] == "listing_changed"
    assert set(event["changed_fields"]) == {
        "reward_status",
        "submission_state",
        "policy_sha256",
    }
    assert event["testing_authorized"] is False


def test_nonmaterial_metadata_change_ignored(tmp_path):
    catalog = make_catalog(tmp_path)

    save(catalog, {
        "alpha": {"updated_at": "2026-01-01"}
    })

    save(catalog, {
        "alpha": {"updated_at": "2026-02-01"}
    })

    result = compare_catalog(catalog.path)

    assert result["status"] == "compared"
    assert result["event_count"] == 0


def test_complete_run_cannot_advertise_more_pages(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}}, more=True)

    with pytest.raises(SnapshotError):
        compare_catalog(catalog.path)


def test_corrupted_page_checksum_rejected(tmp_path):
    catalog = make_catalog(tmp_path)
    save(catalog, {"alpha": {}})

    with sqlite3.connect(catalog.path) as db:
        db.execute(
            "UPDATE pages SET raw=?",
            (b'{"data":[],"links":{}}',),
        )

    with pytest.raises(SnapshotError):
        compare_catalog(catalog.path)


def test_repeated_comparison_is_deterministic(tmp_path):
    catalog = make_catalog(tmp_path)

    save(catalog, {"alpha": {}})
    save(catalog, {"alpha": {}, "beta": {}})

    first = compare_catalog(catalog.path)
    second = compare_catalog(catalog.path)

    assert first == second
    assert first["alerts_issued"] == 0

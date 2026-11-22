"""R10.0A persistent opportunity operations tests."""

import json
import sqlite3
import time

from core.bounty_catalog.store import Catalog
from core.bounty_catalog.operations_r100a import ingest


def catalog_at(tmp_path):
    return Catalog(tmp_path / "catalog.sqlite")


def ledger_at(tmp_path):
    return tmp_path / "private" / "operations.sqlite3"


def save(catalog, records, status="complete", more=False):
    data = [
        {
            "type": "program",
            "attributes": {
                "handle": handle,
                "name": handle,
                "offers_bounties": attributes.get(
                    "paid", True
                ),
                "submission_state": attributes.get(
                    "state", "open"
                ),
                "policy": attributes.get(
                    "policy", "Synthetic policy"
                ),
            },
        }
        for handle, attributes in records.items()
    ]

    links = {}
    if more:
        links["next"] = (
            "https://api.hackerone.com/v1/hackers/programs"
            "?page%5Bnumber%5D=2&page%5Bsize%5D=100"
        )

    now = time.time()
    raw = json.dumps({
        "data": data,
        "links": links,
    }).encode()

    return catalog.save(
        "hackerone-api",
        now,
        [(1, raw, now)],
        status,
    )


def test_first_complete_run_becomes_baseline(tmp_path):
    catalog = catalog_at(tmp_path)
    ledger = ledger_at(tmp_path)

    save(catalog, {"alpha": {}, "beta": {}})
    original = catalog.path.read_bytes()

    result = ingest(catalog.path, ledger)

    assert result["status"] == "baseline_established"
    assert result["current_program_count"] == 2
    assert result["new_events"] == 0
    assert result["total_events"] == 0
    assert result["alerts_issued"] == 0
    assert result["network_requests"] == 0
    assert catalog.path.read_bytes() == original


def test_repeated_ingestion_is_idempotent(tmp_path):
    catalog = catalog_at(tmp_path)
    ledger = ledger_at(tmp_path)

    save(catalog, {"alpha": {}})

    ingest(catalog.path, ledger)
    result = ingest(catalog.path, ledger)

    assert result["status"] == "up_to_date"
    assert result["new_events"] == 0
    assert result["total_events"] == 0


def test_new_changed_and_removed_programs(tmp_path):
    catalog = catalog_at(tmp_path)
    ledger = ledger_at(tmp_path)

    save(catalog, {
        "alpha": {},
        "beta": {"paid": False},
    })

    ingest(catalog.path, ledger)

    save(catalog, {
        "beta": {"paid": True},
        "gamma": {},
    })

    result = ingest(catalog.path, ledger)

    assert result["status"] == "ingested"
    assert result["new_events"] == 3
    assert result["total_events"] == 3
    assert result["notification_authorized"] is False

    with sqlite3.connect(ledger) as db:
        rows = db.execute("""
            SELECT handle, event_type
            FROM opportunity_events
            ORDER BY handle
        """).fetchall()

    assert rows == [
        ("alpha", "no_longer_listed"),
        ("beta", "listing_changed"),
        ("gamma", "new_listing"),
    ]

    again = ingest(catalog.path, ledger)
    assert again["status"] == "up_to_date"
    assert again["total_events"] == 3


def test_multiple_snapshots_processed_in_order(tmp_path):
    catalog = catalog_at(tmp_path)
    ledger = ledger_at(tmp_path)

    save(catalog, {"alpha": {}})
    ingest(catalog.path, ledger)

    save(catalog, {
        "alpha": {},
        "beta": {},
    })

    save(catalog, {
        "alpha": {},
        "beta": {},
        "gamma": {},
    })

    result = ingest(catalog.path, ledger)

    assert result["processed_complete_runs"] == 2
    assert result["new_events"] == 2
    assert result["total_events"] == 2


def test_incomplete_snapshot_never_generates_events(tmp_path):
    catalog = catalog_at(tmp_path)
    ledger = ledger_at(tmp_path)

    save(catalog, {"alpha": {}})
    ingest(catalog.path, ledger)

    save(
        catalog,
        {"beta": {}},
        status="limited",
        more=True,
    )

    blocked = ingest(catalog.path, ledger)

    assert blocked["status"] == (
        "blocked_latest_run_incomplete"
    )

    save(catalog, {"alpha": {}, "gamma": {}})

    result = ingest(catalog.path, ledger)

    assert result["new_events"] == 1
    assert result["total_events"] == 1


def test_missing_catalog_does_not_create_ledger(tmp_path):
    ledger = ledger_at(tmp_path)

    result = ingest(
        tmp_path / "missing.sqlite", ledger
    )

    assert result["status"] == "catalog_missing"
    assert not ledger.exists()

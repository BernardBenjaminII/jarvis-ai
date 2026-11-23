import json
import sqlite3
import time

import pytest

from core.bounty_catalog.store import Catalog
from core.bounty_catalog.operations_r100a import ingest
from core.bounty_catalog.review_queue_r100b import (
    ReviewError,
    list_reviews,
    transition_review,
)


def save(catalog, handles):
    raw = json.dumps({
        "data": [
            {
                "type": "program",
                "attributes": {
                    "handle": handle,
                    "name": handle,
                    "offers_bounties": True,
                    "submission_state": "open",
                    "policy": "Synthetic policy",
                },
            }
            for handle in handles
        ],
        "links": {},
    }).encode()

    now = time.time()
    catalog.save(
        "hackerone-api",
        now,
        [(1, raw, now)],
        "complete",
    )


def seeded_queue(tmp_path):
    catalog = Catalog(tmp_path / "catalog.sqlite")
    ledger = tmp_path / "private" / "operations.sqlite3"

    save(catalog, ["alpha"])
    ingest(catalog.path, ledger)

    save(catalog, ["alpha", "beta", "gamma"])
    ingest(catalog.path, ledger)

    return ledger


def review(ledger, event_id, request_id,
           expected="pending", new="acknowledged",
           note="Reviewed listing"):
    return transition_review(
        event_id,
        expected_state=expected,
        new_state=new,
        actor="test-operator",
        request_id=request_id,
        note=note,
        ledger_path=ledger,
    )


def test_missing_ledger_is_not_created(tmp_path):
    ledger = tmp_path / "missing.sqlite"
    result = list_reviews(ledger)

    assert result["status"] == "ledger_missing"
    assert result["records"] == []
    assert not ledger.exists()


def test_queue_reports_persisted_events(tmp_path):
    ledger = seeded_queue(tmp_path)

    before = ledger.read_bytes()
    result = list_reviews(ledger)

    assert result["status"] == "ready"
    assert result["total_events"] == 2
    assert result["counts"]["pending"] == 2
    assert len(result["records"]) == 2
    assert result["network_requests"] == 0
    assert result["execution_authorized"] is False
    assert ledger.read_bytes() == before


def test_review_transition_persists(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    result = review(ledger, event_id, "review-00001")

    assert result["status"] == "updated"
    assert result["review_state"] == "acknowledged"

    queue = list_reviews(ledger, state="acknowledged")
    assert len(queue["records"]) == 1
    assert queue["records"][0]["id"] == event_id

    with sqlite3.connect(ledger) as db:
        row = db.execute("""
            SELECT from_state, to_state, actor
            FROM review_history
        """).fetchone()

    assert row == (
        "pending",
        "acknowledged",
        "test-operator",
    )


def test_retry_does_not_duplicate_history(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    first = review(ledger, event_id, "review-00002")
    second = review(ledger, event_id, "review-00002")

    assert first["status"] == "updated"
    assert second["status"] == "already_applied"

    with sqlite3.connect(ledger) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM review_history"
        ).fetchone()[0]

    assert count == 1


def test_conflicting_request_id_rejected(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    review(ledger, event_id, "review-00003")

    with pytest.raises(ReviewError):
        review(
            ledger,
            event_id,
            "review-00003",
            expected="acknowledged",
            new="resolved",
        )


def test_stale_review_decision_rejected(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    review(ledger, event_id, "review-00004")

    with pytest.raises(ReviewError):
        review(
            ledger,
            event_id,
            "review-00005",
            expected="pending",
            new="deferred",
        )

    assert list_reviews(ledger)["counts"]["acknowledged"] == 1


def test_resolved_review_can_be_reopened(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    review(
        ledger,
        event_id,
        "review-00006",
        new="resolved",
    )

    reopened = review(
        ledger,
        event_id,
        "review-00007",
        expected="resolved",
        new="pending",
    )

    assert reopened["status"] == "updated"
    assert reopened["review_state"] == "pending"

    with sqlite3.connect(ledger) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM review_history"
        ).fetchone()[0]

    assert count == 2


def test_invalid_actions_do_not_change_state(tmp_path):
    ledger = seeded_queue(tmp_path)
    event_id = list_reviews(ledger)["records"][0]["id"]

    with pytest.raises(ReviewError):
        review(
            ledger,
            event_id,
            "review-00008",
            new="pending",
        )

    with pytest.raises(ReviewError):
        review(
            ledger,
            event_id,
            "bad",
        )

    assert list_reviews(ledger)["counts"]["pending"] == 2


def test_catalog_is_untouched_by_reviews(tmp_path):
    catalog = Catalog(tmp_path / "catalog.sqlite")
    ledger = tmp_path / "private" / "operations.sqlite3"

    save(catalog, ["alpha"])
    ingest(catalog.path, ledger)

    save(catalog, ["alpha", "beta"])
    ingest(catalog.path, ledger)

    before = catalog.path.read_bytes()
    event_id = list_reviews(ledger)["records"][0]["id"]

    review(ledger, event_id, "review-00009")

    assert catalog.path.read_bytes() == before


def test_queue_pagination_and_filtering(tmp_path):
    ledger = seeded_queue(tmp_path)

    first = list_reviews(ledger, limit=1)
    second = list_reviews(ledger, limit=1, offset=1)

    assert len(first["records"]) == 1
    assert len(second["records"]) == 1
    assert first["records"][0]["id"] != second["records"][0]["id"]

    assert list_reviews(
        ledger, state="resolved"
    )["records"] == []

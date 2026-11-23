"""R9.22D1: authenticated, read-only opportunity dashboard API.

No discovery requests, authorization changes, mission creation,
reconnaissance, or report submission.
"""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException, Query

from core.bounty_agent.autonomy.program_scope_store_r921d import ProgramScopeStore
from core.bounty_agent.autonomy.program_opportunities_r922b2 import (
    build_unified_opportunity_queue,
)
from core.bounty_agent.autonomy.program_capability_fit_r922c1 import (
    rank_opportunity_reviews,
)
from core.capabilities.kali_workstation import inventory_snapshot


router = APIRouter(tags=["Bounty Opportunity Intelligence"])

class ReadOnlyScopeStore(ProgramScopeStore):
    """Reuse existing policy validation without mutable initialization."""

    def __init__(self, path):
        self.path = Path(path).expanduser()

        if self.path.is_symlink() or not self.path.is_file():
            raise OSError("Invalid scope database")

    @contextmanager
    def db(self):
        connection = sqlite3.connect(
            self.path.resolve(strict=True).as_uri()
            + "?mode=ro",
            uri=True,
            timeout=10,
        )

        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            yield connection
        finally:
            connection.close()



class ReadOnlyCatalog:
    """Provide the existing catalog connection contract without writes."""

    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        if self.path is None:
            db = sqlite3.connect(":memory:")
            db.execute("""
                CREATE TABLE runs (
                    id TEXT,
                    source TEXT,
                    finished REAL,
                    status TEXT,
                    error TEXT
                )
            """)
        else:
            db = sqlite3.connect(
                self.path.resolve(strict=True).as_uri()
                + "?mode=ro",
                uri=True,
                timeout=5,
            )

        db.row_factory = sqlite3.Row

        try:
            yield db
        finally:
            db.close()


def _catalog_view():
    base = Path(
        os.environ.get(
            "JARVIS_RUNTIME_ROOT",
            str(Path.home() / ".local/share/jarvis"),
        )
    ).expanduser()

    path = base / "bounty_catalog" / "r4.sqlite"

    if path.is_symlink():
        raise OSError("Catalog symlink forbidden")

    if not path.exists():
        return ReadOnlyCatalog(None)

    if not path.is_file():
        raise OSError("Catalog is not a regular file")

    return ReadOnlyCatalog(path)


@router.get("/opportunity-intelligence")
def get_opportunity_intelligence(
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return offline rankings from existing stored evidence."""

    try:
        data_home = Path(
            os.environ.get(
                "XDG_DATA_HOME",
                str(Path.home() / ".local/share"),
            )
        ).expanduser()
        scope_path = (
            data_home / "jarvis" / "program_scopes_r921d.sqlite3"
        )

        if scope_path.is_symlink():
            raise OSError("Scope database symlink forbidden")

        if scope_path.exists():
            if not scope_path.is_file():
                raise OSError("Scope database must be a file")
            store = ReadOnlyScopeStore(scope_path)
            records = [
                store.get_draft(item["id"])
                for item in store.list_drafts(limit)
            ]
        else:
            records = []

        unified = build_unified_opportunity_queue(
            _catalog_view(),
            records,
        )

        ranked = rank_opportunity_reviews(
            unified,
            inventory_snapshot(),
        )

        if (
            ranked.get("network_requests") != 0
            or ranked.get("testing_authorized") is not False
            or ranked.get("automatic_execution_allowed") is not False
            or ranked.get("mission_creation_allowed") is not False
            or ranked.get("submission_authorized") is not False
        ):
            raise ValueError("Unsafe dashboard result")

        return {
            **ranked,
            "dashboard_version": "r922d1",
            "sources": unified["sources"],
            "imported_policy_count": len(records),
            "independent_policy_verification": False,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Opportunity intelligence unavailable",
        ) from exc


# JARVIS_R100C1_SEARCH
# Reuse the established authenticated, offline ranking pipeline.
from typing import Literal


@router.get("/opportunities")
def browse_opportunities(
    search: str = Query(default="", max_length=120),
    source: Literal[
        "all",
        "hackerone_api_snapshot",
        "manual_policy_import",
    ] = Query(default="all"),
    lane: Literal[
        "all",
        "POLICY_REVIEW",
        "MANUAL_A",
        "MANUAL_B",
        "SKIP",
        "IMPORTED_POLICY",
    ] = Query(default="all"),
    limit: int = Query(default=25, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=5000),
):
    """Search and page validated opportunities without writes."""

    # Reuse all existing catalog, policy, and ranking validation.
    # The underlying imported-policy reader currently caps at 200.
    data = get_opportunity_intelligence(limit=200)
    records = data.get("opportunities")

    unsafe = (
        data.get("schema")
        != "jarvis.bounty.program_capability_fit.r922c1"
        or data.get("network_requests") != 0
        or data.get("testing_authorized") is not False
        or data.get("automatic_execution_allowed") is not False
        or data.get("mission_creation_allowed") is not False
        or data.get("submission_authorized") is not False
        or not isinstance(records, list)
        or len(records) > 5000
        or type(data.get("opportunity_count")) is not int
        or data["opportunity_count"] != len(records)
        or not isinstance(data.get("sources"), dict)
    )

    if unsafe:
        raise HTTPException(
            status_code=503,
            detail="Opportunity browser safety validation failed",
        )

    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("human_review_required") is not True
            or record.get("testing_authorized") is not False
            or record.get("execution_enabled") is not False
            or record.get("automatic_execution_ready") is not False
            or record.get("submission_authorized") is not False
            or not all(
                isinstance(record.get(field), str)
                for field in (
                    "program",
                    "platform",
                    "source",
                    "source_identifier",
                    "review_lane",
                )
            )
        ):
            raise HTTPException(
                status_code=503,
                detail="Unsafe opportunity record",
            )

    needle = search.strip().casefold()

    def matches(record):
        if source != "all" and record["source"] != source:
            return False

        if lane != "all" and record["review_lane"] != lane:
            return False

        if needle:
            searchable = (
                record["program"],
                record["platform"],
                record["source_identifier"],
                record["review_lane"],
            )

            if not any(
                needle in value.casefold()
                for value in searchable
            ):
                return False

        return True

    selected = [record for record in records if matches(record)]
    page = selected[offset:offset + limit]

    catalog = data["sources"].get("hackerone_catalog", {})

    if not isinstance(catalog, dict):
        raise HTTPException(
            status_code=503,
            detail="Invalid catalog provenance",
        )

    return {
        "schema": "jarvis.bounty.opportunity_browser.r10c1",
        "mode": "offline_read_only",
        "search": search.strip(),
        "source_filter": source,
        "lane_filter": lane,
        "limit": limit,
        "offset": offset,
        "total_opportunities": len(records),
        "total_matched": len(selected),
        "returned_count": len(page),
        "has_more": offset + len(page) < len(selected),
        "catalog_status": catalog.get("status", "unknown"),
        "imported_policy_count": data.get(
            "imported_policy_count", 0
        ),
        "imported_policy_limit": 200,
        "results": page,
        "workstation": data.get("workstation", {}),
        "network_requests": 0,
        "human_review_required": True,
        "independent_policy_verification": False,
        "testing_authorized": False,
        "automatic_execution_allowed": False,
        "mission_creation_allowed": False,
        "submission_authorized": False,
    }

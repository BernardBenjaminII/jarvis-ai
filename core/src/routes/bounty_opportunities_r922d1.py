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

"""Safe indexed search adapter for JARVIS Arsenal."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from core.security.arsenal_catalog_r32 import (
    DEFAULT_ROOT,
    search_catalog,
    verify_storage,
)

DEFAULT_DATABASE = (
    DEFAULT_ROOT
    / "jarvis_index/catalog/arsenal.sqlite3"
)


def indexed_search(
    query: str,
    *,
    root: Path = DEFAULT_ROOT,
    database: Path | None = None,
    limit: int = 30,
) -> dict:
    query = query.strip()

    if not query or len(query) > 100:
        raise ValueError("Query must contain 1-100 characters")

    limit = max(1, min(int(limit), 50))

    root = Path(root)

    if not verify_storage(root):
        return {
            "state": "offline",
            "results": [],
            "truncated": False,
        }

    if database is None:
        database = (
            root / "jarvis_index/catalog/arsenal.sqlite3"
        )

    database = Path(database)

    if not database.is_file():
        return {
            "state": "index_unavailable",
            "results": [],
            "truncated": False,
        }

    try:
        rows = search_catalog(
            query,
            database=database,
            limit=limit + 1,
        )
    except (sqlite3.DatabaseError, OSError):
        return {
            "state": "index_error",
            "results": [],
            "truncated": False,
        }

    truncated = len(rows) > limit

    return {
        "state": "ready",
        "results": [
            {
                "library": row["library"],
                "path": row["path"],
                "name": row["name"],
            }
            for row in rows[:limit]
        ],
        "truncated": truncated,
    }

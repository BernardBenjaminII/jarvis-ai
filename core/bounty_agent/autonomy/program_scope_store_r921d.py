"""R9.21D: durable, read-only-for-operations policy draft store.

Policy imports are NOT approvals or execution authorizations.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path

from core.bounty_agent.autonomy.program_scope_r921a import (
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    validate_draft,
)


class ProgramScopeStoreError(ValueError):
    pass


class ProgramScopeStore:
    def __init__(self, path):
        self.path = Path(path).expanduser()

        if self.path.is_symlink():
            raise ProgramScopeStoreError(
                "Symlink database path forbidden"
            )

        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )

        if self.path.exists():
            os.chmod(self.path, 0o600)

        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS scope_drafts (
                    id TEXT PRIMARY KEY,
                    policy_sha256 TEXT NOT NULL UNIQUE,
                    platform TEXT NOT NULL,
                    program TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scope_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draft_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    FOREIGN KEY(draft_id)
                        REFERENCES scope_drafts(id)
                );
            """)

        os.chmod(self.path, 0o600)

    def db(self):
        db = sqlite3.connect(
            self.path,
            timeout=10
        )
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def canonical_snapshot(draft):
        # Validate the original record first.
        validate_draft(draft)

        # Reconstruct only known fields, discarding unknown input.
        snapshot = create_scope_draft(
            platform=draft["platform"],
            program=draft["program"],
            policy_url=draft["policy_url"],
            in_scope=draft["in_scope"],
            out_of_scope=draft["out_of_scope"],
            restrictions=draft["restrictions"],
        )

        if snapshot["policy_sha256"] != draft["policy_sha256"]:
            raise ProgramScopeStoreError(
                "Policy digest mismatch"
            )

        return snapshot

    def import_draft(self, draft):
        snapshot = self.canonical_snapshot(draft)
        digest = snapshot["policy_sha256"]
        content = json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":")
        )

        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")

            existing = db.execute(
                """
                SELECT id, content_json
                FROM scope_drafts
                WHERE policy_sha256 = ?
                """,
                (digest,),
            ).fetchone()

            if existing:
                stored = json.loads(existing["content_json"])
                self.canonical_snapshot(stored)

                if stored["policy_sha256"] != digest:
                    raise ProgramScopeStoreError(
                        "Stored policy digest mismatch"
                    )

                return existing["id"]

            draft_id = str(uuid.uuid4())

            db.execute(
                """
                INSERT INTO scope_drafts
                (id, policy_sha256, platform, program,
                 content_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    draft_id,
                    digest,
                    snapshot["platform"],
                    snapshot["program"],
                    content,
                    snapshot["imported_at"],
                ),
            )

            db.execute(
                """
                INSERT INTO scope_events
                (draft_id, event_type, event_at)
                VALUES (?, 'draft_imported', ?)
                """,
                (draft_id, snapshot["imported_at"]),
            )

        return draft_id

    def get_draft(self, draft_id):
        with self.db() as db:
            row = db.execute(
                """
                SELECT * FROM scope_drafts WHERE id = ?
                """,
                (draft_id,),
            ).fetchone()

        if row is None:
            raise ProgramScopeStoreError(
                "Unknown policy draft"
            )

        try:
            draft = json.loads(row["content_json"])
            self.canonical_snapshot(draft)

            if (
                draft["policy_sha256"] != row["policy_sha256"]
                or draft["platform"] != row["platform"]
                or draft["program"] != row["program"]
            ):
                raise ProgramScopeStoreError(
                    "Stored policy metadata mismatch"
                )

        except (ValueError, TypeError, KeyError) as exc:
            raise ProgramScopeStoreError(
                "Stored policy integrity failure"
            ) from exc

        return {
            "id": row["id"],
            "draft": draft,
            "review_status": "unverified",
            "execution_authorized": False,
            "submission_authorized": False,
        }

    def list_drafts(self, limit=50):
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ProgramScopeStoreError("Invalid list limit")

        with self.db() as db:
            rows = db.execute(
                """
                SELECT id FROM scope_drafts
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        # Validate each record before exposing its metadata.
        results = []
        for row in rows:
            record = self.get_draft(row["id"])
            draft = record["draft"]

            results.append({
                "id": record["id"],
                "platform": draft["platform"],
                "program": draft["program"],
                "policy_sha256": draft["policy_sha256"],
                "review_status": "unverified",
                "execution_authorized": False,
            })

        return results

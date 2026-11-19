"""R9.21E3: durable operator-attested scope reviews.

Policy reviews remain advisory-only.
No authorization creation, mission planning, or tool execution.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path

from core.bounty_agent.autonomy.program_scope_review_r921b import (
    assess_reviewed_target,
    review_scope_draft,
    validate_draft,
)


class ScopeReviewStoreError(ValueError):
    pass


class ScopeReviewStore:
    def __init__(self, path):
        self.path = Path(path).expanduser()

        if self.path.is_symlink():
            raise ScopeReviewStoreError("Symlink database forbidden")

        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )

        if self.path.exists():
            os.chmod(self.path, 0o600)

        with self.db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS scope_reviews (
                    id TEXT PRIMARY KEY,
                    draft_id TEXT NOT NULL,
                    policy_sha256 TEXT NOT NULL,
                    review_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

        os.chmod(self.path, 0o600)

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def attest(
        self,
        *,
        draft_id,
        draft,
        reviewer,
        source_checked_at,
        source_matches,
    ):
        if not isinstance(draft_id, str) or not draft_id.strip():
            raise ScopeReviewStoreError("Draft identifier required")

        # Generate the review server-side using existing validation.
        review = review_scope_draft(
            draft,
            reviewer=reviewer,
            source_checked_at=source_checked_at,
            source_matches=source_matches,
        )

        review_id = str(uuid.uuid4())

        with self.db() as db:
            db.execute(
                """
                INSERT INTO scope_reviews
                (id, draft_id, policy_sha256,
                 review_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    draft_id,
                    review["policy_sha256"],
                    json.dumps(review, sort_keys=True),
                    review["reviewed_at"],
                ),
            )

        return {
            "id": review_id,
            "draft_id": draft_id,
            "review_status": "operator_attested",
            "execution_authorized": False,
            "submission_authorized": False,
        }

    def get(self, review_id, *, draft_id, draft):
        if not isinstance(review_id, str) or not review_id.strip():
            raise ScopeReviewStoreError("Invalid review identifier")

        digest = validate_draft(draft)

        with self.db() as db:
            row = db.execute(
                """
                SELECT * FROM scope_reviews
                WHERE id = ? AND draft_id = ?
                """,
                (review_id, draft_id),
            ).fetchone()

        if row is None:
            raise ScopeReviewStoreError("Unknown review")

        if row["policy_sha256"] != digest:
            raise ScopeReviewStoreError("Policy digest mismatch")

        try:
            review = json.loads(row["review_json"])

            # Revalidate the stored review and its expiry.
            assess_reviewed_target(
                draft,
                review,
                draft["in_scope"][0],
            )
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            raise ScopeReviewStoreError(
                "Review invalid or expired"
            ) from exc

        return {
            "id": review_id,
            "draft_id": draft_id,
            "review": review,
            "execution_authorized": False,
            "submission_authorized": False,
        }

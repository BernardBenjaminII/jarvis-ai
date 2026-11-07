"""R9.14D.6A: durable, non-executing operation approvals.

Creating an approval record is NOT proof of authenticated
human consent. Production issuance requires a separate,
trusted reviewer-authentication boundary.
"""

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path


class ApprovalDenied(ValueError):
    pass


class ApprovalStore:
    def __init__(self, path, authorization_store):
        self.path = Path(path).expanduser()
        self.authorization_store = authorization_store
        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )

        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    authorization TEXT NOT NULL,
                    program TEXT NOT NULL,
                    target TEXT NOT NULL,
                    policy_digest TEXT NOT NULL,
                    scope_digest TEXT NOT NULL,
                    budget INTEGER NOT NULL,
                    reviewer TEXT NOT NULL,
                    created REAL NOT NULL,
                    expires REAL NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0,
                    record_digest TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approval_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT NOT NULL,
                    at REAL NOT NULL,
                    kind TEXT NOT NULL,
                    detail TEXT
                );
            """)

        os.chmod(self.path, 0o600)

    def db(self):
        db = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
        )
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @staticmethod
    def digest(record):
        fields = (
            "id", "authorization", "program", "target",
            "policy_digest", "scope_digest", "budget",
            "reviewer", "created", "expires",
        )
        payload = {
            field: record[field] for field in fields
        }
        return hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    def issue(
        self,
        *,
        authorization,
        program,
        target,
        policy_digest,
        budget,
        reviewer,
        ttl=3600,
    ):
        """Administrative issuance API; not a user-auth gate."""
        if type(budget) is not int or not 1 <= budget <= 10:
            raise ApprovalDenied("Invalid budget")

        if type(ttl) is not int or not 60 <= ttl <= 86400:
            raise ApprovalDenied("Invalid approval TTL")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                authorization, program, target,
                policy_digest, reviewer,
            )
        ):
            raise ApprovalDenied("Invalid approval identifiers")

        scope = self.authorization_store.live_scope(
            authorization
        )
        auth = self.authorization_store.get(authorization)

        if scope.program != program:
            raise ApprovalDenied("Program mismatch")

        if target.startswith("*.") or target not in scope.include:
            raise ApprovalDenied(
                "Target must be an explicitly included host"
            )

        if target in scope.exclude:
            raise ApprovalDenied("Target explicitly excluded")

        now = time.time()
        expires = min(now + ttl, auth["expires"])

        record = {
            "id": str(uuid.uuid4()),
            "authorization": authorization,
            "program": program,
            "target": target,
            "policy_digest": policy_digest,
            "scope_digest": auth["scope_sha256"],
            "budget": budget,
            "reviewer": reviewer,
            "created": now,
            "expires": expires,
        }
        digest = self.digest(record)

        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    """
                    INSERT INTO approvals(
                        id,authorization,program,target,
                        policy_digest,scope_digest,budget,
                        reviewer,created,expires,record_digest
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        record["id"], authorization, program,
                        target, policy_digest,
                        record["scope_digest"], budget,
                        reviewer, now, expires, digest,
                    ),
                )
                db.execute(
                    """
                    INSERT INTO approval_events(
                        approval_id,at,kind,detail
                    ) VALUES(?,?,'issued',?)
                    """,
                    (record["id"], now, reviewer),
                )
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

        return record["id"]

    def verify(
        self,
        approval_id,
        *,
        authorization,
        program,
        target,
        policy_digest,
        budget,
    ):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM approvals WHERE id=?",
                (approval_id,),
            ).fetchone()

        if row is None:
            raise ApprovalDenied("Unknown approval")

        record = dict(row)

        if self.digest(record) != record["record_digest"]:
            raise ApprovalDenied("Approval integrity mismatch")

        if record["revoked"]:
            raise ApprovalDenied("Approval revoked")

        if time.time() >= record["expires"]:
            raise ApprovalDenied("Approval expired")

        expected = {
            "authorization": authorization,
            "program": program,
            "target": target,
            "policy_digest": policy_digest,
            "budget": budget,
        }

        for field, value in expected.items():
            if record[field] != value:
                raise ApprovalDenied(
                    f"Approval {field} mismatch"
                )

        scope = self.authorization_store.live_scope(
            authorization
        )
        auth = self.authorization_store.get(authorization)

        if auth["scope_sha256"] != record["scope_digest"]:
            raise ApprovalDenied("Authorization scope changed")

        if (
            scope.program != program
            or target.startswith("*.")
            or target not in scope.include
            or target in scope.exclude
        ):
            raise ApprovalDenied("Target no longer approved")

        return True

    def revoke(self, approval_id, reason=""):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT id FROM approvals WHERE id=?",
                    (approval_id,),
                ).fetchone()

                if row is None:
                    raise ApprovalDenied("Unknown approval")

                db.execute(
                    """
                    UPDATE approvals SET revoked=1
                    WHERE id=?
                    """,
                    (approval_id,),
                )
                db.execute(
                    """
                    INSERT INTO approval_events(
                        approval_id,at,kind,detail
                    ) VALUES(?,?,'revoked',?)
                    """,
                    (approval_id, time.time(), reason),
                )
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

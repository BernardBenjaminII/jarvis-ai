"""R9.14D.1: durable, fail-closed mission claims.

Claim acquisition is atomic. This module does not execute
reconnaissance or create live missions.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path


class MissionClaimStore:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )

        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_key TEXT PRIMARY KEY,
                    authorization TEXT NOT NULL,
                    program TEXT NOT NULL,
                    target TEXT NOT NULL,
                    policy_digest TEXT NOT NULL,
                    state TEXT NOT NULL,
                    session_id TEXT,
                    mission_id TEXT,
                    created REAL NOT NULL,
                    updated REAL NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS claim_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_key TEXT NOT NULL,
                    at REAL NOT NULL,
                    kind TEXT NOT NULL,
                    detail TEXT
                );
            """)

        # Additive migration; legacy claims remain unapproved.
        with self.connect() as db:
            columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(claims)"
                )
            }
            if "approval_id" not in columns:
                db.execute(
                    "ALTER TABLE claims ADD COLUMN approval_id TEXT"
                )

        self._enforce_active_claim_uniqueness()
        self.path.chmod(0o600)

    def _enforce_active_claim_uniqueness(self):
        """R9.14D.5A: fail closed on cross-policy duplicates.

        Both claimed and created are considered active until
        a separately reviewed lifecycle is implemented.
        """
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                conflicts = db.execute(
                    """
                    SELECT authorization, program, target,
                           COUNT(*) AS total
                    FROM claims
                    WHERE state IN ('claimed', 'created')
                    GROUP BY authorization, program, target
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                ).fetchone()

                if conflicts:
                    raise ValueError(
                        "Conflicting active scheduler claims "
                        "require manual reconciliation"
                    )

                db.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                    active_claim_target_unique
                    ON claims(authorization, program, target)
                    WHERE state IN ('claimed', 'created')
                    """
                )
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def connect(self):
        db = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
        )
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @staticmethod
    def key(authorization, program, target, policy_digest):
        values = (
            authorization,
            program,
            target,
            policy_digest,
        )
        if not all(
            isinstance(value, str) and value.strip()
            for value in values
        ):
            raise ValueError("Claim identifiers must be nonempty")

        payload = "\x00".join(values)
        return hashlib.sha256(payload.encode()).hexdigest()

    def claim(
        self,
        *,
        authorization,
        program,
        target,
        policy_digest,
        approval_id=None,
    ):
        if approval_id is not None and (
            not isinstance(approval_id, str)
            or not approval_id.strip()
        ):
            raise ValueError("Invalid approval ID")

        key = self.key(
            authorization, program, target, policy_digest
        )
        now = time.time()

        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                active = db.execute(
                    """
                    SELECT claim_key, policy_digest
                    FROM claims
                    WHERE authorization=?
                      AND program=?
                      AND target=?
                      AND state IN ('claimed', 'created')
                    """,
                    (authorization, program, target),
                ).fetchone()

                if (
                    active is not None
                    and active["claim_key"] != key
                ):
                    raise sqlite3.IntegrityError(
                        "Active claim exists under a different "
                        "policy digest; manual reconciliation required"
                    )

                inserted = db.execute(
                    """
                    INSERT OR IGNORE INTO claims(
                        claim_key, authorization, program,
                        target, policy_digest, state,
                        created, updated, approval_id
                    ) VALUES(?,?,?,?,?,'claimed',?,?,?)
                    """,
                    (
                        key, authorization, program,
                        target, policy_digest, now, now,
                        approval_id,
                    ),
                ).rowcount == 1

                if inserted:
                    db.execute(
                        """
                        INSERT INTO claim_events(
                            claim_key,at,kind,detail
                        ) VALUES(?,?,'claimed','atomic claim acquired')
                        """,
                        (key, now),
                    )

                row = db.execute(
                    "SELECT * FROM claims WHERE claim_key=?",
                    (key,),
                ).fetchone()

                if row is None:
                    raise RuntimeError("Claim disappeared")

                if row["approval_id"] != approval_id:
                    raise sqlite3.IntegrityError(
                        "Claim approval identity mismatch; "
                        "manual reconciliation required"
                    )

                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

        return {
            "acquired": inserted,
            "claim": dict(row),
        }

    def get(self, key):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM claims WHERE claim_key=?",
                (key,),
            ).fetchone()
        return dict(row) if row else None

    def mark_created(self, key, session_id, mission_id):
        """Atomically complete a claim; identical retries are safe."""
        if not session_id or not mission_id:
            raise ValueError("Session and mission IDs required")

        now = time.time()

        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                claim = db.execute(
                    "SELECT * FROM claims WHERE claim_key=?",
                    (key,),
                ).fetchone()

                if claim is None:
                    raise ValueError("Unknown claim")

                if claim["state"] == "created":
                    if (
                        claim["session_id"] != session_id
                        or claim["mission_id"] != mission_id
                    ):
                        raise ValueError(
                            "Claim already belongs to another "
                            "session or mission"
                        )

                    db.execute("COMMIT")
                    return False

                if claim["state"] != "claimed":
                    raise ValueError(
                        "Claim not in claimed state"
                    )

                db.execute(
                    """
                    UPDATE claims
                    SET state='created',
                        session_id=?,
                        mission_id=?,
                        updated=?
                    WHERE claim_key=?
                      AND state='claimed'
                    """,
                    (session_id, mission_id, now, key),
                )

                db.execute(
                    """
                    INSERT INTO claim_events(
                        claim_key,at,kind,detail
                    ) VALUES(?,?,'created',?)
                    """,
                    (key, now, session_id),
                )

                db.execute("COMMIT")
                return True

            except BaseException:
                db.execute("ROLLBACK")
                raise

    def pending(self):
        with self.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    """
                    SELECT * FROM claims
                    WHERE state='claimed'
                    ORDER BY created,claim_key
                    """
                )
            ]

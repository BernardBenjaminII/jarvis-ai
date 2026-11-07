"""R9.15A.11F: atomic first-key enrollment coordination."""

import hashlib
import secrets
import time


class FirstKeyEnrollment:
    def __init__(self, store):
        self.store = store
        with store.connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS first_key_enrollment (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    ticket_digest TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    challenge_id TEXT,
                    expires_at INTEGER NOT NULL
                )
            """)

    def issue(self, reviewer, ttl=300):
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Reviewer required")
        if not 1 <= ttl <= 300:
            raise ValueError("Invalid ticket lifetime")
        ticket = secrets.token_urlsafe(32)
        digest = hashlib.sha256(ticket.encode()).hexdigest()
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM credentials LIMIT 1").fetchone():
                raise PermissionError("First key already registered")
            db.execute("""
                INSERT INTO first_key_enrollment
                    (singleton, ticket_digest, reviewer, challenge_id, expires_at)
                VALUES (1, ?, ?, NULL, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    ticket_digest = excluded.ticket_digest,
                    reviewer = excluded.reviewer,
                    challenge_id = NULL,
                    expires_at = excluded.expires_at
            """, (digest, reviewer, int(time.time()) + ttl))
        return ticket

    def bind_challenge(self, ticket, reviewer, challenge_id):
        if not isinstance(ticket, str) or not ticket or not challenge_id:
            raise PermissionError("Invalid enrollment ticket")
        digest = hashlib.sha256(ticket.encode()).hexdigest()
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM credentials LIMIT 1").fetchone():
                raise PermissionError("First key already registered")
            result = db.execute("""
                UPDATE first_key_enrollment SET challenge_id = ?
                WHERE singleton = 1 AND ticket_digest = ?
                  AND reviewer = ? AND challenge_id IS NULL
                  AND expires_at > ?
            """, (challenge_id, digest, reviewer, int(time.time())))
            if result.rowcount != 1:
                raise PermissionError("Invalid or consumed enrollment ticket")


    def register_verified_first_key(
        self,
        reviewer,
        challenge_id,
        expected_challenge,
        credential_id,
        public_key,
        sign_count,
    ):
        """Commit a previously verified registration atomically."""
        if (
            not reviewer
            or not challenge_id
            or not expected_challenge
            or not credential_id
            or not public_key
            or sign_count < 0
        ):
            raise ValueError("Invalid verified registration")

        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")

            now = int(time.time())

            authorization = db.execute(
                """
                SELECT reviewer, expires_at
                FROM first_key_enrollment
                WHERE singleton = 1
                  AND challenge_id = ?
                """,
                (challenge_id,),
            ).fetchone()

            if (
                authorization is None
                or authorization[0] != reviewer
                or authorization[1] <= now
            ):
                raise PermissionError(
                    "Enrollment authorization invalid"
                )

            challenge = db.execute(
                """
                SELECT challenge, expires_at
                FROM challenges
                WHERE id = ? AND reviewer = ?
                """,
                (challenge_id, reviewer),
            ).fetchone()

            if (
                challenge is None
                or challenge[1] <= now
                or not secrets.compare_digest(
                    challenge[0], expected_challenge
                )
            ):
                raise PermissionError(
                    "Challenge invalid or consumed"
                )

            if db.execute(
                "SELECT 1 FROM credentials LIMIT 1"
            ).fetchone():
                raise PermissionError(
                    "First key already registered"
                )

            db.execute(
                """
                INSERT INTO credentials
                (
                    credential_id,
                    reviewer,
                    public_key,
                    sign_count,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    credential_id,
                    reviewer,
                    public_key,
                    sign_count,
                    now,
                ),
            )

            db.execute(
                "DELETE FROM challenges WHERE id = ?",
                (challenge_id,),
            )

            db.execute(
                "DELETE FROM first_key_enrollment WHERE singleton = 1"
            )

    def register_first_key(self, reviewer, challenge_id, credential_id, public_key, sign_count):
        raise PermissionError("Unverified registration disabled")

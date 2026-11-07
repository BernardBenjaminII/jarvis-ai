"""R9.15A.11E: local first-key enrollment bootstrap."""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path

from .store import CredentialStore


def default_store_path() -> Path:
    return (
        Path.home()
        / ".local/share/jarvis/bounty_agent"
        / "webauthn"
        / "credentials.sqlite"
    )


class EnrollmentBootstrap:
    def __init__(self, store: CredentialStore):
        self.store = store

        with self.store.connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS enrollment_tickets (
                    digest TEXT PRIMARY KEY,
                    reviewer TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)

    def issue(self, reviewer: str, ttl: int = 300) -> str:
        raise PermissionError("Legacy bootstrap disabled")

    def consume(self, token: str, reviewer: str):
        if not isinstance(token, str) or not token:
            raise PermissionError("Invalid enrollment ticket")

        digest = hashlib.sha256(token.encode()).hexdigest()

        with self.store.connection() as db:
            record = db.execute(
                """
                DELETE FROM enrollment_tickets
                WHERE digest = ?
                  AND reviewer = ?
                RETURNING expires_at
                """,
                (digest, reviewer),
            ).fetchone()

        if record is None or record[0] <= int(time.time()):
            raise PermissionError(
                "Enrollment ticket expired or invalid"
            )


def issue_local_ticket(reviewer: str):
    store = CredentialStore(default_store_path())
    bootstrap = EnrollmentBootstrap(store)
    return bootstrap.issue(reviewer)

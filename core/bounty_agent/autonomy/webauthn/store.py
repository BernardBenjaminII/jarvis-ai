"""R9.15A.11D: private WebAuthn credential storage."""

from __future__ import annotations

import os
import secrets
import sqlite3
import stat
import time
from contextlib import contextmanager
from pathlib import Path


class CredentialStore:
    def __init__(self, path: Path):
        self.path = Path(path)

        if not self.path.is_absolute():
            raise ValueError("Absolute database path required")

        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)

        if parent.is_symlink():
            raise PermissionError("Symlinked storage directory")

        info = parent.stat()

        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise PermissionError("Unsafe storage directory")

        flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC

        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        fd = os.open(self.path, flags, 0o600)

        try:
            info = os.fstat(fd)

            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
                or info.st_nlink != 1
            ):
                raise PermissionError("Unsafe database file")
        finally:
            os.close(fd)

        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY,
                    reviewer TEXT NOT NULL,
                    challenge BLOB NOT NULL,
                    expires_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS credentials (
                    credential_id BLOB PRIMARY KEY,
                    reviewer TEXT NOT NULL,
                    public_key BLOB NOT NULL,
                    sign_count INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(
            self.path,
            timeout=5,
        )

        try:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA journal_mode=DELETE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_challenge(
        self,
        reviewer: str,
        ttl: int = 300,
    ):
        if not reviewer or not reviewer.strip():
            raise ValueError("Reviewer required")

        if not 1 <= ttl <= 300:
            raise ValueError("Invalid challenge lifetime")

        challenge_id = secrets.token_urlsafe(32)
        challenge = secrets.token_bytes(32)

        with self.connection() as db:
            db.execute(
                """
                INSERT INTO challenges
                (id, reviewer, challenge, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    challenge_id,
                    reviewer,
                    challenge,
                    int(time.time()) + ttl,
                ),
            )

        return challenge_id, challenge

    def consume_challenge(
        self,
        challenge_id: str,
        reviewer: str,
    ):
        now = int(time.time())

        with self.connection() as db:
            record = db.execute(
                """
                DELETE FROM challenges
                WHERE id = ?
                  AND reviewer = ?
                RETURNING challenge, expires_at
                """,
                (challenge_id, reviewer),
            ).fetchone()

        if record is None:
            raise ValueError("Unknown or consumed challenge")

        challenge, expires_at = record

        if expires_at <= now:
            raise ValueError("Expired challenge")

        return challenge

    def register(
        self,
        reviewer: str,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
    ):
        if not reviewer or not credential_id or not public_key:
            raise ValueError("Invalid credential")

        if sign_count < 0:
            raise ValueError("Invalid signature counter")

        with self.connection() as db:
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
                    int(time.time()),
                ),
            )

    def close(self):
        """Compatibility with the original store interface."""
        pass

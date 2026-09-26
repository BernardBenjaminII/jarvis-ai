from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

from core.bounty_scope import LiveScope, ScopeDenied


class AuthorizationDenied(ValueError):
    pass


def _default_db():
    root = os.environ.get("JARVIS_RUNTIME_ROOT")

    if root:
        return Path(root) / "bounty_authorization" / "r5_1.sqlite"

    return Path.home() / ".local/share/jarvis/bounty_authorization/r5_1.sqlite"


class AuthorizationStore:
    def __init__(self, path=None):
        self.path = Path(path or _default_db()).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._init()

        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _init(self):
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS authorizations (
                id TEXT PRIMARY KEY,
                program TEXT NOT NULL,
                scope_json TEXT NOT NULL,
                scope_sha256 TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                reviewed_at REAL NOT NULL,
                expires REAL NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                note TEXT
            );

            CREATE INDEX IF NOT EXISTS auth_program_idx
                ON authorizations(program);

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                authorization TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT,
                FOREIGN KEY(authorization) REFERENCES authorizations(id)
            );
            """)

    def _event(self, db, auth_id, kind, detail=""):
        db.execute(
            "INSERT INTO events(authorization,at,kind,detail) VALUES(?,?,?,?)",
            (auth_id, time.time(), kind, detail),
        )

    def create(
        self,
        *,
        program,
        include,
        exclude=(),
        capabilities=("subfinder", "httpx"),
        reviewer,
        source_material,
        ttl=86400,
        note="",
    ):
        if type(ttl) is not int or not 60 <= ttl <= 2592000:
            raise AuthorizationDenied("TTL must be between 60 seconds and 30 days")

        scope = LiveScope.reviewed(
            program=program,
            include=include,
            exclude=exclude,
            allowed_capabilities=capabilities,
            reviewed_by=reviewer,
            source_material=source_material,
        )

        evidence = scope.evidence()

        auth_id = str(uuid.uuid4())

        # Persist only the canonical scope payload.
        # scope_sha256 is derived from this payload and stored separately.
        scope_payload = {
            "program": evidence["program"],
            "include": evidence["include"],
            "exclude": evidence["exclude"],
            "allowed_capabilities": evidence["allowed_capabilities"],
            "reviewed_by": evidence["reviewed_by"],
            "source_digest": evidence["source_digest"],
            "reviewed_at": evidence["reviewed_at"],
        }

        scope_json = json.dumps(scope_payload, sort_keys=True)

        expires = time.time() + ttl

        with self.db() as db:
            db.execute(
                """
                INSERT INTO authorizations(
                    id,program,scope_json,scope_sha256,source_sha256,
                    reviewer,reviewed_at,expires,revoked,note
                ) VALUES(?,?,?,?,?,?,?,?,0,?)
                """,
                (
                    auth_id,
                    scope.program,
                    scope_json,
                    evidence["scope_sha256"],
                    evidence["source_digest"],
                    scope.reviewed_by,
                    scope.reviewed_at,
                    expires,
                    note,
                ),
            )

            self._event(db, auth_id, "created", "Reviewed live authorization created")

        return auth_id

    def revoke(self, auth_id, reason=""):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM authorizations WHERE id=?",
                (auth_id,),
            ).fetchone()

            if not row:
                raise AuthorizationDenied("Unknown authorization")

            db.execute(
                "UPDATE authorizations SET revoked=1 WHERE id=?",
                (auth_id,),
            )

            self._event(db, auth_id, "revoked", reason)

    def get(self, auth_id):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM authorizations WHERE id=?",
                (auth_id,),
            ).fetchone()

        if not row:
            raise AuthorizationDenied("Unknown authorization")

        return dict(row)

    def live_scope(self, auth_id):
        row = self.get(auth_id)

        if row["revoked"]:
            raise AuthorizationDenied("Authorization revoked")

        if time.time() >= row["expires"]:
            raise AuthorizationDenied("Authorization expired")

        try:
            raw = json.loads(row["scope_json"])
        except json.JSONDecodeError as exc:
            raise AuthorizationDenied("Authorization record corrupted") from exc

        check = hashlib.sha256(
            json.dumps(raw, sort_keys=True).encode()
        ).hexdigest()

        if check != row["scope_sha256"]:
            raise AuthorizationDenied("Scope digest mismatch")

        scope = LiveScope(
            program=raw["program"],
            include=tuple(raw["include"]),
            exclude=tuple(raw["exclude"]),
            allowed_capabilities=tuple(raw["allowed_capabilities"]),
            reviewed_by=raw["reviewed_by"],
            source_digest=raw["source_digest"],
            reviewed_at=raw["reviewed_at"],
        )

        return scope

    def events(self, auth_id):
        with self.db() as db:
            return [
                dict(x)
                for x in db.execute(
                    "SELECT * FROM events WHERE authorization=? ORDER BY id",
                    (auth_id,),
                ).fetchall()
            ]

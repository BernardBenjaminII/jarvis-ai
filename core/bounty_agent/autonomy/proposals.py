"""R9.15A.3: persistent, non-executing mission proposals."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path


class ProposalError(ValueError):
    pass


class ProposalStore:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(
            parents=True, exist_ok=True, mode=0o700
        )
        with self.db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    proposal_key TEXT NOT NULL,
                    program TEXT NOT NULL,
                    target TEXT NOT NULL,
                    authorization_id TEXT NOT NULL,
                    policy_digest TEXT NOT NULL,
                    budget INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created REAL NOT NULL,
                    expires REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                one_pending_proposal
                ON proposals(proposal_key)
                WHERE status='pending'
            """)
        self.path.chmod(0o600)

    def db(self):
        db = sqlite3.connect(
            self.path, timeout=10
        )
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def key(program, target, authorization_id,
            policy_digest, budget):
        payload = json.dumps(
            [program, target, authorization_id,
             policy_digest, budget],
            separators=(",", ":"),
        )
        return hashlib.sha256(
            payload.encode()
        ).hexdigest()

    def create(
        self, *,
        program,
        target,
        authorization_id,
        policy_digest,
        budget=2,
        ttl=3600,
    ):
        if type(budget) is not int or not 1 <= budget <= 10:
            raise ProposalError("Invalid budget")

        if type(ttl) is not int or not 60 <= ttl <= 86400:
            raise ProposalError("Invalid TTL")

        values = (
            program, target, authorization_id, policy_digest
        )
        if not all(
            isinstance(value, str) and value.strip()
            for value in values
        ):
            raise ProposalError("Invalid proposal identifiers")

        key = self.key(
            program, target, authorization_id,
            policy_digest, budget
        )
        now = time.time()

        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                UPDATE proposals
                SET status='expired'
                WHERE status='pending' AND expires<=?
            """, (now,))

            existing = db.execute("""
                SELECT * FROM proposals
                WHERE proposal_key=? AND status='pending'
            """, (key,)).fetchone()

            if existing:
                return dict(existing)

            record = {
                "id": str(uuid.uuid4()),
                "proposal_key": key,
                "program": program,
                "target": target,
                "authorization_id": authorization_id,
                "policy_digest": policy_digest,
                "budget": budget,
                "status": "pending",
                "created": now,
                "expires": now + ttl,
            }

            db.execute("""
                INSERT INTO proposals VALUES (
                    :id, :proposal_key, :program, :target,
                    :authorization_id, :policy_digest,
                    :budget, :status, :created, :expires
                )
            """, record)

            return record

    def get(self, proposal_id):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM proposals WHERE id=?",
                (proposal_id,),
            ).fetchone()
        return dict(row) if row else None

    def pending(self):
        now = time.time()
        with self.db() as db:
            db.execute("""
                UPDATE proposals
                SET status='expired'
                WHERE status='pending' AND expires<=?
            """, (now,))
            rows = db.execute("""
                SELECT * FROM proposals
                WHERE status='pending'
                ORDER BY created, id
            """).fetchall()
        return [dict(row) for row in rows]

    def cancel(self, proposal_id):
        with self.db() as db:
            cursor = db.execute("""
                UPDATE proposals
                SET status='cancelled'
                WHERE id=? AND status='pending'
                  AND expires>?
            """, (proposal_id, time.time()))

        if cursor.rowcount != 1:
            raise ProposalError(
                "Proposal missing or no longer pending"
            )

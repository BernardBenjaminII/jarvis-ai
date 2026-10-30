from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time
import uuid

from .model import (
    ProgramAsset,
    ProgramIntakeDraft,
    ProgramSnapshot,
)


class ProgramStore:
    def __init__(self, path=None):
        if path is None:
            path = (
                Path.home()
                / ".local/share/jarvis"
                / "bounty_programs.sqlite"
            )

        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._init_db()

    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self):
        with self.db() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS programs(
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    handle TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    source_digest TEXT NOT NULL,
                    created REAL NOT NULL
                )
                """
            )

            db.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_programs_source_handle
                ON programs(source,handle)
                """
            )


            db.execute(
                """
                CREATE TABLE IF NOT EXISTS
                program_drafts(
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    handle TEXT NOT NULL,
                    name TEXT NOT NULL,
                    draft_json TEXT NOT NULL,
                    source_digest TEXT NOT NULL,
                    created REAL NOT NULL
                )
                """
            )

            db.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_program_drafts_source_handle
                ON program_drafts(source,handle)
                """
            )

    def save(
        self,
        snapshot: ProgramSnapshot,
    ) -> str:
        program_id = str(uuid.uuid4())

        payload = snapshot.canonical_json()

        with self.db() as db:
            db.execute(
                """
                INSERT INTO programs(
                    id,
                    source,
                    handle,
                    name,
                    source_url,
                    snapshot_json,
                    source_digest,
                    created
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    program_id,
                    snapshot.source,
                    snapshot.handle,
                    snapshot.name,
                    snapshot.source_url,
                    payload,
                    snapshot.source_digest,
                    time.time(),
                ),
            )

        return program_id

    def get(self, program_id: str) -> dict:
        with self.db() as db:
            row = db.execute(
                """
                SELECT *
                FROM programs
                WHERE id=?
                """,
                (program_id,),
            ).fetchone()

        if not row:
            raise KeyError(
                "Unknown bounty program"
            )

        item = dict(row)
        item["snapshot"] = json.loads(
            item.pop("snapshot_json")
        )

        return item

    def list(self, limit=50) -> list[dict]:
        with self.db() as db:
            rows = db.execute(
                """
                SELECT
                    id,
                    source,
                    handle,
                    name,
                    source_url,
                    source_digest,
                    created
                FROM programs
                ORDER BY created DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def save_draft(
        self,
        draft: ProgramIntakeDraft,
    ) -> str:
        draft_id = str(uuid.uuid4())

        with self.db() as db:
            db.execute(
                """
                INSERT INTO program_drafts(
                    id,
                    source,
                    handle,
                    name,
                    draft_json,
                    source_digest,
                    created
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    draft_id,
                    draft.source,
                    draft.handle,
                    draft.name,
                    draft.canonical_json(),
                    draft.source_digest,
                    time.time(),
                ),
            )

        return draft_id

    def get_draft(
        self,
        draft_id: str,
    ) -> dict:
        with self.db() as db:
            row = db.execute(
                """
                SELECT *
                FROM program_drafts
                WHERE id=?
                """,
                (draft_id,),
            ).fetchone()

        if not row:
            raise KeyError(
                "Unknown bounty program draft"
            )

        item = dict(row)
        item["draft"] = json.loads(
            item.pop("draft_json")
        )

        return item

    def list_drafts(
        self,
        limit=50,
    ) -> list[dict]:
        with self.db() as db:
            rows = db.execute(
                """
                SELECT
                    id,
                    source,
                    handle,
                    name,
                    source_digest,
                    created
                FROM program_drafts
                ORDER BY created DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .contracts import Candidate, CandidateDisposition, CandidateResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS campaign_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campaign_candidates (
    candidate_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    extension TEXT NOT NULL,
    sha256 TEXT,
    title TEXT,
    category TEXT,
    source_json TEXT NOT NULL,
    disposition TEXT NOT NULL DEFAULT 'PENDING',
    detail TEXT NOT NULL DEFAULT '',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_campaign_candidates_disposition
ON campaign_candidates(disposition);

CREATE TABLE IF NOT EXISTS campaign_batches (
    batch_id TEXT PRIMARY KEY,
    ordinal INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    report_json TEXT
);

CREATE TABLE IF NOT EXISTS campaign_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    candidate_id TEXT,
    batch_id TEXT,
    detail TEXT NOT NULL
);
"""


class CheckpointStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def set_state(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO campaign_state(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )
            connection.commit()

    def get_state(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM campaign_state WHERE key=?",
                (key,),
            ).fetchone()
            return None if row is None else str(row["value"])

    def register_candidates(self, candidates: Iterable[Candidate]) -> int:
        inserted = 0
        with self._connect() as connection:
            for candidate in candidates:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO campaign_candidates(
                        candidate_id, path, extension, sha256,
                        title, category, source_json
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.candidate_id,
                        candidate.path,
                        candidate.extension,
                        candidate.sha256,
                        candidate.title,
                        candidate.category,
                        json.dumps(candidate.source_row, sort_keys=True),
                    ),
                )
                inserted += int(cursor.rowcount > 0)
            connection.commit()
        return inserted

    def next_candidates(
        self,
        *,
        limit: int,
        retry_failures: bool,
    ) -> tuple[Candidate, ...]:
        dispositions = [CandidateDisposition.PENDING.value]
        if retry_failures:
            dispositions.extend(
                (
                    CandidateDisposition.FAILED_EXTRACTION.value,
                    CandidateDisposition.FAILED_MATERIALIZATION.value,
                )
            )
        placeholders = ",".join("?" for _ in dispositions)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM campaign_candidates
                WHERE disposition IN ({placeholders})
                ORDER BY candidate_id
                LIMIT ?
                """,
                (*dispositions, limit),
            ).fetchall()

        return tuple(
            Candidate(
                candidate_id=str(row["candidate_id"]),
                path=str(row["path"]),
                extension=str(row["extension"]),
                sha256=row["sha256"],
                title=row["title"],
                category=row["category"],
                source_row=json.loads(row["source_json"]),
            )
            for row in rows
        )

    def mark_attempt(self, candidate_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE campaign_candidates
                SET attempt_count=attempt_count+1,
                    last_attempt_at=?
                WHERE candidate_id=?
                """,
                (now, candidate_id),
            )
            connection.commit()

    def record_result(self, result: CandidateResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE campaign_candidates
                SET disposition=?,
                    detail=?,
                    completed_at=?
                WHERE candidate_id=?
                """,
                (
                    result.disposition.value,
                    result.detail,
                    now,
                    result.candidate_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO campaign_events(
                    occurred_at, event_type, candidate_id, detail
                )
                VALUES(?, ?, ?, ?)
                """,
                (
                    now,
                    "candidate_result",
                    result.candidate_id,
                    json.dumps(result.to_dict(), sort_keys=True),
                ),
            )
            connection.commit()

    def start_batch(
        self,
        *,
        batch_id: str,
        ordinal: int,
        candidate_count: int,
        started_at: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO campaign_batches(
                    batch_id, ordinal, started_at, status, candidate_count
                )
                VALUES(?, ?, ?, 'RUNNING', ?)
                """,
                (batch_id, ordinal, started_at, candidate_count),
            )
            connection.commit()

    def complete_batch(
        self,
        *,
        batch_id: str,
        completed_at: str,
        status: str,
        report_json: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE campaign_batches
                SET completed_at=?, status=?, report_json=?
                WHERE batch_id=?
                """,
                (completed_at, status, report_json, batch_id),
            )
            connection.commit()

    def disposition_counts(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT disposition, COUNT(*) AS count
                FROM campaign_candidates
                GROUP BY disposition
                ORDER BY disposition
                """
            ).fetchall()
        return {
            str(row["disposition"]): int(row["count"])
            for row in rows
        }

    def candidate_count(self) -> int:
        with self._connect() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM campaign_candidates"
                ).fetchone()[0]
            )

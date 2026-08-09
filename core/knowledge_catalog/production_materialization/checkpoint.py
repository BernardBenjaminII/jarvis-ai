from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import MaterializationStage, WorkItem


SCHEMA = """
CREATE TABLE IF NOT EXISTS items(
    candidate_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    extension TEXT NOT NULL,
    sha256 TEXT,
    stage TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 0,
    extraction_seconds REAL NOT NULL DEFAULT 0,
    write_seconds REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_items_stage
ON items(stage);

CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    candidate_id TEXT,
    event_type TEXT NOT NULL,
    stage TEXT,
    detail TEXT NOT NULL
);
"""


RECOVERABLE_INCOMPLETE_STAGES = (
    MaterializationStage.EXTRACTING.value,
    MaterializationStage.EXTRACTED.value,
    MaterializationStage.CHUNKED.value,
    MaterializationStage.WRITING.value,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CheckpointStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=30.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def register(self, items) -> int:
        inserted = 0
        stamp = now()

        with self._connect() as connection:
            for item in items:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO items(
                        candidate_id,
                        path,
                        title,
                        category,
                        extension,
                        sha256,
                        stage,
                        created_at,
                        updated_at
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.candidate_id,
                        item.path,
                        item.title,
                        item.category,
                        item.extension,
                        item.sha256,
                        MaterializationStage.DISCOVERED.value,
                        stamp,
                        stamp,
                    ),
                )
                inserted += int(cursor.rowcount > 0)

            connection.commit()

        return inserted

    def recover_incomplete_states(self) -> dict[str, int]:
        placeholders = ",".join(
            "?" for _ in RECOVERABLE_INCOMPLETE_STAGES
        )
        stamp = now()

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT stage, COUNT(*) AS count
                FROM items
                WHERE stage IN ({placeholders})
                GROUP BY stage
                """,
                RECOVERABLE_INCOMPLETE_STAGES,
            ).fetchall()

            counts = {
                str(row["stage"]): int(row["count"])
                for row in rows
            }

            connection.execute(
                f"""
                UPDATE items
                SET stage=?,
                    detail=?,
                    updated_at=?
                WHERE stage IN ({placeholders})
                """,
                (
                    MaterializationStage.VALIDATED.value,
                    "Recovered after interrupted or stopped run; re-extraction required.",
                    stamp,
                    *RECOVERABLE_INCOMPLETE_STAGES,
                ),
            )

            recovered_total = sum(counts.values())

            if recovered_total:
                connection.execute(
                    """
                    INSERT INTO events(
                        occurred_at,
                        candidate_id,
                        event_type,
                        stage,
                        detail
                    )
                    VALUES(?, NULL, 'recovery', ?, ?)
                    """,
                    (
                        stamp,
                        MaterializationStage.VALIDATED.value,
                        (
                            "Recovered incomplete states: "
                            + ", ".join(
                                f"{stage}={count}"
                                for stage, count in sorted(counts.items())
                            )
                        ),
                    ),
                )

            connection.commit()

        return counts

    def recover_transient_lock_failures(self) -> int:
        stamp = now()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE items
                SET stage=?,
                    detail=?,
                    updated_at=?
                WHERE stage=?
                  AND lower(detail) LIKE '%database is locked%'
                """,
                (
                    MaterializationStage.VALIDATED.value,
                    "Recovered transient SQLite lock failure.",
                    stamp,
                    MaterializationStage.FAILED.value,
                ),
            )
            recovered = int(cursor.rowcount)

            if recovered:
                connection.execute(
                    """
                    INSERT INTO events(
                        occurred_at,
                        candidate_id,
                        event_type,
                        stage,
                        detail
                    )
                    VALUES(?, NULL, 'recovery', ?, ?)
                    """,
                    (
                        stamp,
                        MaterializationStage.VALIDATED.value,
                        f"Recovered {recovered} transient lock failures.",
                    ),
                )

            connection.commit()

        return recovered

    def next_items(
        self,
        limit: int,
        retry_failures: bool = False,
    ):
        stages = [
            MaterializationStage.DISCOVERED.value,
            MaterializationStage.VALIDATED.value,
        ]

        if retry_failures:
            stages.extend(
                (
                    MaterializationStage.FAILED.value,
                    MaterializationStage.QUARANTINED.value,
                )
            )

        placeholders = ",".join("?" for _ in stages)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM items
                WHERE stage IN ({placeholders})
                ORDER BY candidate_id
                LIMIT ?
                """,
                (*stages, limit),
            ).fetchall()

        return tuple(
            WorkItem(
                candidate_id=str(row["candidate_id"]),
                path=str(row["path"]),
                title=str(row["title"]),
                category=row["category"],
                extension=str(row["extension"]),
                sha256=row["sha256"],
            )
            for row in rows
        )

    def set_stage(
        self,
        candidate_id,
        stage,
        detail,
        attempt=False,
        extraction_seconds=None,
        write_seconds=None,
    ) -> None:
        fields = [
            "stage=?",
            "detail=?",
            "updated_at=?",
        ]
        values = [
            stage.value,
            detail,
            now(),
        ]

        if attempt:
            fields.append("attempts=attempts+1")

        if extraction_seconds is not None:
            fields.append("extraction_seconds=?")
            values.append(float(extraction_seconds))

        if write_seconds is not None:
            fields.append("write_seconds=?")
            values.append(float(write_seconds))

        values.append(candidate_id)

        with self._connect() as connection:
            connection.execute(
                f"""
                UPDATE items
                SET {", ".join(fields)}
                WHERE candidate_id=?
                """,
                values,
            )
            connection.execute(
                """
                INSERT INTO events(
                    occurred_at,
                    candidate_id,
                    event_type,
                    stage,
                    detail
                )
                VALUES(?, ?, 'stage_transition', ?, ?)
                """,
                (
                    now(),
                    candidate_id,
                    stage.value,
                    detail,
                ),
            )
            connection.commit()

    def counts(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT stage, COUNT(*) AS count
                FROM items
                GROUP BY stage
                """
            ).fetchall()

        return {
            str(row["stage"]): int(row["count"])
            for row in rows
        }

    def total(self) -> int:
        with self._connect() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM items"
                ).fetchone()[0]
            )

    def pending(self) -> int:
        with self._connect() as connection:
            return int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM items
                    WHERE stage IN (?, ?)
                    """,
                    (
                        MaterializationStage.DISCOVERED.value,
                        MaterializationStage.VALIDATED.value,
                    ),
                ).fetchone()[0]
            )

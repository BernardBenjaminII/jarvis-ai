"""
SQLite repository for JARVIS Phase VII-B2 source registry.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .contracts import RegisteredSource, RegistryStats, SourceLifecycleState
from .errors import SourceRegistryNotFoundError


class SQLiteSourceRegistryRepository:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)

    @property
    def db_path(self) -> str:
        return self._db_path

    def initialize(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_registry (
                    registry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    canonical_location TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    trust_tier TEXT NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    host TEXT,
                    lifecycle_state TEXT NOT NULL,
                    admitted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_source_registry_state
                    ON source_registry(lifecycle_state);

                CREATE INDEX IF NOT EXISTS idx_source_registry_host
                    ON source_registry(host);
                """
            )
            conn.commit()

    def insert(
        self,
        *,
        source_id: str,
        display_name: str,
        canonical_location: str,
        kind: str,
        trust_tier: str,
        fingerprint: str,
        host: str | None,
        lifecycle_state: SourceLifecycleState,
        admitted_at: str,
        updated_at: str,
        metadata: dict,
    ) -> RegisteredSource:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                INSERT INTO source_registry (
                    source_id,
                    display_name,
                    canonical_location,
                    kind,
                    trust_tier,
                    fingerprint,
                    host,
                    lifecycle_state,
                    admitted_at,
                    updated_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    display_name,
                    canonical_location,
                    kind,
                    trust_tier,
                    fingerprint,
                    host,
                    lifecycle_state.value,
                    admitted_at,
                    updated_at,
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            conn.commit()
            return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, registry_id: int) -> RegisteredSource:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM source_registry WHERE registry_id = ?",
                (registry_id,),
            ).fetchone()
        if row is None:
            raise SourceRegistryNotFoundError(
                f"Source registry entry not found: {registry_id}"
            )
        return self._row_to_source(row)

    def get_by_source_id(self, source_id: str) -> RegisteredSource | None:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM source_registry WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return None if row is None else self._row_to_source(row)

    def get_by_fingerprint(self, fingerprint: str) -> RegisteredSource | None:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM source_registry WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        return None if row is None else self._row_to_source(row)

    def list_all(self) -> list[RegisteredSource]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM source_registry ORDER BY registry_id"
            ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def update_state(
        self,
        registry_id: int,
        state: SourceLifecycleState,
        updated_at: str,
    ) -> RegisteredSource:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE source_registry
                SET lifecycle_state = ?, updated_at = ?
                WHERE registry_id = ?
                """,
                (state.value, updated_at, registry_id),
            )
            conn.commit()
            if cursor.rowcount != 1:
                raise SourceRegistryNotFoundError(
                    f"Source registry entry not found: {registry_id}"
                )
        return self.get_by_id(registry_id)

    def stats(self) -> RegistryStats:
        counts = {
            state.value: 0
            for state in SourceLifecycleState
        }

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT lifecycle_state, COUNT(*)
                FROM source_registry
                GROUP BY lifecycle_state
                """
            ).fetchall()

        for state, count in rows:
            counts[state] = count

        return RegistryStats(
            total=sum(counts.values()),
            admitted=counts[SourceLifecycleState.ADMITTED.value],
            active=counts[SourceLifecycleState.ACTIVE.value],
            paused=counts[SourceLifecycleState.PAUSED.value],
            retired=counts[SourceLifecycleState.RETIRED.value],
        )

    @staticmethod
    def _row_to_source(row: sqlite3.Row) -> RegisteredSource:
        return RegisteredSource(
            registry_id=int(row["registry_id"]),
            source_id=str(row["source_id"]),
            display_name=str(row["display_name"]),
            canonical_location=str(row["canonical_location"]),
            kind=str(row["kind"]),
            trust_tier=str(row["trust_tier"]),
            fingerprint=str(row["fingerprint"]),
            host=row["host"],
            lifecycle_state=SourceLifecycleState(
                str(row["lifecycle_state"])
            ),
            admitted_at=str(row["admitted_at"]),
            updated_at=str(row["updated_at"]),
            metadata=json.loads(str(row["metadata_json"])),
        )

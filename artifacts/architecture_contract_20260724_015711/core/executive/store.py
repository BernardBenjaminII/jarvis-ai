"""SQLite persistence for JARVIS Gen 2 missions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from core.executive.contracts import MissionNotFoundError
from core.executive.models import Mission


class MissionStore:
    """Thread-safe SQLite repository storing complete mission snapshots."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS mission_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_missions_status
                ON missions(status)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_mission_id
                ON mission_events(mission_id)
                """
            )

    def save(self, mission: Mission) -> None:
        payload = json.dumps(
            mission.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO missions (
                    mission_id,
                    objective,
                    status,
                    payload_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                    objective = excluded.objective,
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    mission.mission_id,
                    mission.objective,
                    mission.status.value,
                    payload,
                    mission.created_at,
                    mission.updated_at,
                ),
            )

    def load(self, mission_id: str) -> Mission:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()

        if row is None:
            raise MissionNotFoundError(f"Mission not found: {mission_id}")

        data = json.loads(row["payload_json"])
        return Mission.from_dict(data)

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mission]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        query = "SELECT payload_json FROM missions"
        parameters: list[Any] = []
        if status:
            query += " WHERE status = ?"
            parameters.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        parameters.append(limit)

        with self._lock, self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [
            Mission.from_dict(json.loads(row["payload_json"]))
            for row in rows
        ]

    def record_event(
        self,
        mission_id: str,
        event_type: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO mission_events (
                    mission_id,
                    event_type,
                    payload_json,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    mission_id,
                    event_type,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )

    def events(self, mission_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, payload_json, created_at
                FROM mission_events
                WHERE mission_id = ?
                ORDER BY event_id ASC
                """,
                (mission_id,),
            ).fetchall()

        return [
            {
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

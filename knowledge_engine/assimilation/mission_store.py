"""
Persistent mission and checkpoint storage for JARVIS assimilation.
"""

from __future__ import annotations

import json
from typing import Any

from knowledge_engine.assimilation.mission import (
    AssimilationMission,
    AssimilationMissionItem,
    MissionStatus,
    utc_now,
)
from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)


class MissionNotFoundError(LookupError):
    """Raised when a requested persistent mission does not exist."""


class AssimilationMissionStore:
    """Persist missions and item-level checkpoints in the catalog."""

    def __init__(self, db: Any):
        self.db = db

    def save_new(self, mission: AssimilationMission) -> None:
        """Persist a newly planned mission and all mission items."""

        payload = mission.to_dict()

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            existing = conn.execute(
                """
                SELECT 1
                FROM knowledge_assimilation_missions
                WHERE mission_id=?
                """,
                (mission.mission_id,),
            ).fetchone()

            if existing is not None:
                raise ValueError(
                    f"Mission already exists: {mission.mission_id}"
                )

            self._upsert_mission_row(
                conn=conn,
                mission=mission,
                payload=payload,
            )

            for item in mission.items:
                self._upsert_item_row(
                    conn=conn,
                    mission_id=mission.mission_id,
                    item=item,
                )

            conn.commit()

    def checkpoint(
        self,
        mission: AssimilationMission,
        *,
        item: AssimilationMissionItem | None = None,
        last_error: str | None = None,
    ) -> None:
        """Persist mission progress and optionally one changed item."""

        payload = mission.to_dict()

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            self._upsert_mission_row(
                conn=conn,
                mission=mission,
                payload=payload,
                last_error=last_error,
            )

            if item is not None:
                self._upsert_item_row(
                    conn=conn,
                    mission_id=mission.mission_id,
                    item=item,
                )

            conn.commit()

    def load(self, mission_id: str) -> AssimilationMission:
        """Load a complete mission from its durable JSON checkpoint."""

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)

            row = conn.execute(
                """
                SELECT mission_json
                FROM knowledge_assimilation_missions
                WHERE mission_id=?
                """,
                (mission_id,),
            ).fetchone()

        if row is None:
            raise MissionNotFoundError(
                f"Assimilation mission not found: {mission_id}"
            )

        payload = json.loads(str(row["mission_json"]))
        return AssimilationMission.from_dict(payload)

    def history(
        self,
        *,
        limit: int = 25,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return recent persistent mission summaries."""

        if limit < 1:
            raise ValueError("limit must be at least 1")

        query = """
            SELECT
                mission_id,
                fingerprint,
                mission_status,
                created_at,
                started_at,
                paused_at,
                completed_at,
                last_checkpoint_at,
                processed_count,
                failed_count,
                skipped_count,
                blocked_count,
                total_items,
                last_error
            FROM knowledge_assimilation_missions
        """

        parameters: list[Any] = []

        if status is not None:
            query += " WHERE mission_status=?"
            parameters.append(status)

        query += """
            ORDER BY last_checkpoint_at DESC, created_at DESC
            LIMIT ?
        """
        parameters.append(limit)

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)

            rows = conn.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return [
            {
                "mission_id": str(row["mission_id"]),
                "fingerprint": str(row["fingerprint"]),
                "status": str(row["mission_status"]),
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "paused_at": row["paused_at"],
                "completed_at": row["completed_at"],
                "last_checkpoint_at": row["last_checkpoint_at"],
                "processed": int(row["processed_count"]),
                "failed": int(row["failed_count"]),
                "skipped": int(row["skipped_count"]),
                "blocked": int(row["blocked_count"]),
                "total_items": int(row["total_items"]),
                "last_error": row["last_error"],
            }
            for row in rows
        ]

    def mission_items(
        self,
        mission_id: str,
    ) -> list[dict[str, Any]]:
        """Return durable item checkpoints for one mission."""

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)

            rows = conn.execute(
                """
                SELECT
                    sequence,
                    object_uuid,
                    object_path,
                    object_type,
                    handler_name,
                    item_status,
                    message,
                    result_json,
                    started_at,
                    completed_at,
                    updated_at
                FROM knowledge_assimilation_mission_items
                WHERE mission_id=?
                ORDER BY sequence ASC
                """,
                (mission_id,),
            ).fetchall()

        return [
            {
                "sequence": int(row["sequence"]),
                "object_uuid": str(row["object_uuid"]),
                "object_path": str(row["object_path"]),
                "object_type": str(row["object_type"]),
                "handler_name": str(row["handler_name"]),
                "status": str(row["item_status"]),
                "message": row["message"],
                "result": (
                    json.loads(str(row["result_json"]))
                    if row["result_json"]
                    else None
                ),
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    @staticmethod
    def _upsert_mission_row(
        *,
        conn: Any,
        mission: AssimilationMission,
        payload: dict[str, Any],
        last_error: str | None = None,
    ) -> None:
        summary = payload["summary"]

        conn.execute(
            """
            INSERT INTO knowledge_assimilation_missions (
                mission_id,
                fingerprint,
                mission_status,
                database_path,
                requested_limit,
                requested_object_types_json,
                planning_notes_json,
                created_at,
                started_at,
                paused_at,
                completed_at,
                last_checkpoint_at,
                processed_count,
                failed_count,
                skipped_count,
                blocked_count,
                total_items,
                mission_json,
                last_error
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP,
                ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(mission_id) DO UPDATE SET
                fingerprint=excluded.fingerprint,
                mission_status=excluded.mission_status,
                started_at=excluded.started_at,
                paused_at=excluded.paused_at,
                completed_at=excluded.completed_at,
                last_checkpoint_at=CURRENT_TIMESTAMP,
                processed_count=excluded.processed_count,
                failed_count=excluded.failed_count,
                skipped_count=excluded.skipped_count,
                blocked_count=excluded.blocked_count,
                total_items=excluded.total_items,
                planning_notes_json=excluded.planning_notes_json,
                mission_json=excluded.mission_json,
                last_error=excluded.last_error
            """,
            (
                mission.mission_id,
                mission.fingerprint,
                mission.status.value,
                mission.database_path,
                mission.requested_limit,
                json.dumps(
                    mission.requested_object_types,
                    sort_keys=True,
                ),
                json.dumps(
                    mission.planning_notes,
                    sort_keys=True,
                ),
                mission.created_at,
                mission.started_at,
                mission.paused_at,
                mission.completed_at,
                int(summary["processed"]),
                int(summary["failed"]),
                int(summary["skipped"]),
                int(summary["blocked"]),
                int(summary["total_items"]),
                json.dumps(payload, sort_keys=True),
                last_error,
            ),
        )

    @staticmethod
    def _upsert_item_row(
        *,
        conn: Any,
        mission_id: str,
        item: AssimilationMissionItem,
    ) -> None:
        payload = item.to_dict()

        conn.execute(
            """
            INSERT INTO knowledge_assimilation_mission_items (
                mission_id,
                sequence,
                object_uuid,
                object_path,
                object_type,
                handler_name,
                item_status,
                message,
                result_json,
                started_at,
                completed_at,
                updated_at,
                item_json
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP,
                ?
            )
            ON CONFLICT(mission_id, sequence) DO UPDATE SET
                object_uuid=excluded.object_uuid,
                object_path=excluded.object_path,
                object_type=excluded.object_type,
                handler_name=excluded.handler_name,
                item_status=excluded.item_status,
                message=excluded.message,
                result_json=excluded.result_json,
                started_at=excluded.started_at,
                completed_at=excluded.completed_at,
                updated_at=CURRENT_TIMESTAMP,
                item_json=excluded.item_json
            """,
            (
                mission_id,
                item.sequence,
                item.object_uuid,
                item.object_path,
                item.object_type,
                item.handler_name,
                item.status.value,
                item.message,
                (
                    json.dumps(item.result, sort_keys=True)
                    if item.result is not None
                    else None
                ),
                item.started_at,
                item.completed_at,
                json.dumps(payload, sort_keys=True),
            ),
        )

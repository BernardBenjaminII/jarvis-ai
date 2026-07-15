"""
SQL ownership for durable acquisition missions.

The repository does not create connections or own commit and rollback.
"""

from __future__ import annotations

import sqlite3

from knowledge_engine.acquisition.missions.models import (
    AcquisitionMissionItemRecord,
    AcquisitionMissionItemState,
    AcquisitionMissionRecord,
    AcquisitionMissionState,
)


class AcquisitionMissionRepository:
    """Persist and retrieve durable acquisition missions."""

    def mission_exists(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
    ) -> bool:
        row = conn.execute(
            """
            SELECT 1
            FROM acquisition_missions
            WHERE mission_id=?
            LIMIT 1
            """,
            (mission_id,),
        ).fetchone()

        return row is not None

    def insert_mission(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
        request_id: str,
        provider_id: str,
        campaign_id: str | None,
        mission_state: str,
        timestamp: str,
        item_count: int,
        accepted_count: int,
        review_count: int,
        ignored_count: int,
        rejected_count: int,
    ) -> None:
        conn.execute(
            """
            INSERT INTO acquisition_missions (
                mission_id,
                request_id,
                provider_id,
                campaign_id,
                mission_state,
                created_at,
                updated_at,
                item_count,
                accepted_count,
                review_count,
                ignored_count,
                rejected_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                request_id,
                provider_id,
                campaign_id,
                mission_state,
                timestamp,
                timestamp,
                item_count,
                accepted_count,
                review_count,
                ignored_count,
                rejected_count,
            ),
        )

    def insert_item(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
        item_order: int,
        candidate_id: str,
        provider_id: str,
        source_uri: str,
        local_path: str,
        checksum_sha256: str,
        item_state: str,
        decision_fingerprint: str,
        timestamp: str,
    ) -> int:
        cursor = conn.execute(
            """
            INSERT INTO acquisition_mission_items (
                mission_id,
                item_order,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                item_state,
                decision_fingerprint,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                item_order,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                item_state,
                decision_fingerprint,
                timestamp,
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError(
                "Mission item insert did not return an ID"
            )

        return int(cursor.lastrowid)

    def get_mission(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
    ) -> AcquisitionMissionRecord:
        row = conn.execute(
            """
            SELECT
                mission_id,
                request_id,
                provider_id,
                mission_state,
                created_at,
                updated_at,
                item_count,
                accepted_count,
                review_count,
                ignored_count,
                rejected_count,
                campaign_id
            FROM acquisition_missions
            WHERE mission_id=?
            """,
            (mission_id,),
        ).fetchone()

        if row is None:
            raise LookupError(
                f"No acquisition mission: {mission_id}"
            )

        return AcquisitionMissionRecord(
            mission_id=str(row[0]),
            request_id=str(row[1]),
            provider_id=str(row[2]),
            mission_state=AcquisitionMissionState(
                str(row[3])
            ),
            created_at=str(row[4]),
            updated_at=str(row[5]),
            item_count=int(row[6]),
            accepted_count=int(row[7]),
            review_count=int(row[8]),
            ignored_count=int(row[9]),
            rejected_count=int(row[10]),
            campaign_id=(
                str(row[11])
                if row[11] is not None
                else None
            ),
        )

    def list_items(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
    ) -> tuple[AcquisitionMissionItemRecord, ...]:
        rows = conn.execute(
            """
            SELECT
                item_id,
                mission_id,
                item_order,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                item_state,
                decision_fingerprint,
                created_at
            FROM acquisition_mission_items
            WHERE mission_id=?
            ORDER BY item_order
            """,
            (mission_id,),
        ).fetchall()

        return tuple(
            AcquisitionMissionItemRecord(
                item_id=int(row[0]),
                mission_id=str(row[1]),
                item_order=int(row[2]),
                candidate_id=str(row[3]),
                provider_id=str(row[4]),
                source_uri=str(row[5]),
                local_path=str(row[6]),
                checksum_sha256=str(row[7]),
                item_state=AcquisitionMissionItemState(
                    str(row[8])
                ),
                decision_fingerprint=str(row[9]),
                created_at=str(row[10]),
            )
            for row in rows
        )


__all__ = [
    "AcquisitionMissionRepository",
]

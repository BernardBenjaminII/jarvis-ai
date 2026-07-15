"""
SQL ownership for acquisition-to-assimilation handoffs.

The repository owns handoff persistence only. It does not execute
assimilation, begin transactions, commit, or roll back.
"""

from __future__ import annotations

import sqlite3

from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
    AssimilationHandoffState,
)


class AssimilationHandoffRepository:
    """Persist and retrieve durable assimilation handoffs."""

    def handoff_exists(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
        mission_item_id: int,
    ) -> bool:
        row = conn.execute(
            """
            SELECT 1
            FROM acquisition_assimilation_handoffs
            WHERE mission_id=?
              AND mission_item_id=?
            LIMIT 1
            """,
            (
                mission_id,
                mission_item_id,
            ),
        ).fetchone()

        return row is not None

    def insert_handoff(
        self,
        *,
        conn: sqlite3.Connection,
        handoff_id: str,
        mission_id: str,
        mission_item_id: int,
        candidate_id: str,
        provider_id: str,
        source_uri: str,
        local_path: str,
        checksum_sha256: str,
        decision_fingerprint: str,
        timestamp: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO acquisition_assimilation_handoffs (
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                handoff_state,
                created_at,
                updated_at,
                dispatch_attempt_count,
                assimilation_reference,
                last_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, 0, NULL, NULL)
            """,
            (
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                timestamp,
                timestamp,
            ),
        )

    def get_handoff(
        self,
        *,
        conn: sqlite3.Connection,
        handoff_id: str,
    ) -> AssimilationHandoffRecord:
        row = conn.execute(
            """
            SELECT
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                handoff_state,
                created_at,
                updated_at,
                dispatch_attempt_count,
                assimilation_reference,
                last_error
            FROM acquisition_assimilation_handoffs
            WHERE handoff_id=?
            """,
            (handoff_id,),
        ).fetchone()

        if row is None:
            raise LookupError(
                f"No assimilation handoff: {handoff_id}"
            )

        return self._map_handoff(row)

    def get_by_mission_item(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
        mission_item_id: int,
    ) -> AssimilationHandoffRecord:
        row = conn.execute(
            """
            SELECT
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                handoff_state,
                created_at,
                updated_at,
                dispatch_attempt_count,
                assimilation_reference,
                last_error
            FROM acquisition_assimilation_handoffs
            WHERE mission_id=?
              AND mission_item_id=?
            """,
            (
                mission_id,
                mission_item_id,
            ),
        ).fetchone()

        if row is None:
            raise LookupError(
                "No handoff for mission item "
                f"{mission_id}:{mission_item_id}"
            )

        return self._map_handoff(row)

    def list_for_mission(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        rows = conn.execute(
            """
            SELECT
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                handoff_state,
                created_at,
                updated_at,
                dispatch_attempt_count,
                assimilation_reference,
                last_error
            FROM acquisition_assimilation_handoffs
            WHERE mission_id=?
            ORDER BY mission_item_id
            """,
            (mission_id,),
        ).fetchall()

        return tuple(
            self._map_handoff(row)
            for row in rows
        )

    def list_queued(
        self,
        *,
        conn: sqlite3.Connection,
        limit: int,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        if limit < 1:
            raise ValueError(
                "limit must be at least 1"
            )

        rows = conn.execute(
            """
            SELECT
                handoff_id,
                mission_id,
                mission_item_id,
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                checksum_sha256,
                decision_fingerprint,
                handoff_state,
                created_at,
                updated_at,
                dispatch_attempt_count,
                assimilation_reference,
                last_error
            FROM acquisition_assimilation_handoffs
            WHERE handoff_state='queued'
            ORDER BY created_at, handoff_id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return tuple(
            self._map_handoff(row)
            for row in rows
        )

    @staticmethod
    def _map_handoff(
        row: sqlite3.Row | tuple[object, ...],
    ) -> AssimilationHandoffRecord:
        return AssimilationHandoffRecord(
            handoff_id=str(row[0]),
            mission_id=str(row[1]),
            mission_item_id=int(row[2]),
            candidate_id=str(row[3]),
            provider_id=str(row[4]),
            source_uri=str(row[5]),
            local_path=str(row[6]),
            checksum_sha256=str(row[7]),
            decision_fingerprint=str(row[8]),
            handoff_state=AssimilationHandoffState(
                str(row[9])
            ),
            created_at=str(row[10]),
            updated_at=str(row[11]),
            dispatch_attempt_count=int(row[12]),
            assimilation_reference=(
                str(row[13])
                if row[13] is not None
                else None
            ),
            last_error=(
                str(row[14])
                if row[14] is not None
                else None
            ),
        )


__all__ = [
    "AssimilationHandoffRepository",
]

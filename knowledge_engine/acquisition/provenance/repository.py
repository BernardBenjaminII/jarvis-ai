"""
SQL ownership for JARVIS acquisition provenance.

The repository owns provenance reads and writes. It does not open connections,
begin transactions, commit, or execute admission policies.
"""

from __future__ import annotations

import sqlite3

from knowledge_engine.acquisition.provenance.models import (
    AdmissionHistoryRecord,
    ProvenanceRecord,
)


class ProvenanceRepository:
    """Persist and retrieve acquisition provenance records."""

    def source_exists(
        self,
        *,
        conn: sqlite3.Connection,
        provider_id: str,
        source_uri: str,
    ) -> bool:
        row = conn.execute(
            """
            SELECT 1
            FROM acquisition_provenance
            WHERE provider_id=?
              AND source_uri=?
            LIMIT 1
            """,
            (
                provider_id,
                source_uri,
            ),
        ).fetchone()

        return row is not None

    def upsert_sighting(
        self,
        *,
        conn: sqlite3.Connection,
        candidate_id: str,
        provider_id: str,
        source_uri: str,
        local_path: str,
        filename: str,
        checksum_sha256: str,
        seen_at: str,
        action: str,
        decision_fingerprint: str,
        campaign_id: str | None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO acquisition_provenance (
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                filename,
                checksum_sha256,
                first_seen_at,
                last_seen_at,
                sighting_count,
                last_action,
                last_decision_fingerprint,
                campaign_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(provider_id, source_uri) DO UPDATE SET
                local_path=excluded.local_path,
                filename=excluded.filename,
                checksum_sha256=excluded.checksum_sha256,
                last_seen_at=excluded.last_seen_at,
                sighting_count=(
                    acquisition_provenance.sighting_count + 1
                ),
                last_action=excluded.last_action,
                last_decision_fingerprint=(
                    excluded.last_decision_fingerprint
                ),
                campaign_id=COALESCE(
                    excluded.campaign_id,
                    acquisition_provenance.campaign_id
                )
            """,
            (
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                filename,
                checksum_sha256,
                seen_at,
                seen_at,
                action,
                decision_fingerprint,
                campaign_id,
            ),
        )

    def append_history(
        self,
        *,
        conn: sqlite3.Connection,
        candidate_id: str,
        seen_at: str,
        action: str,
        decision_fingerprint: str,
        decision_json: str,
        campaign_id: str | None,
    ) -> int:
        cursor = conn.execute(
            """
            INSERT INTO acquisition_admission_history (
                candidate_id,
                seen_at,
                action,
                decision_fingerprint,
                decision_json,
                campaign_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                seen_at,
                action,
                decision_fingerprint,
                decision_json,
                campaign_id,
            ),
        )

        history_id = cursor.lastrowid

        if history_id is None:
            raise RuntimeError(
                "Admission history insert did not return an ID"
            )

        return int(history_id)

    def get_by_source(
        self,
        *,
        conn: sqlite3.Connection,
        provider_id: str,
        source_uri: str,
    ) -> ProvenanceRecord | None:
        row = conn.execute(
            """
            SELECT
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                filename,
                checksum_sha256,
                first_seen_at,
                last_seen_at,
                sighting_count,
                last_action,
                last_decision_fingerprint,
                campaign_id
            FROM acquisition_provenance
            WHERE provider_id=?
              AND source_uri=?
            """,
            (
                provider_id,
                source_uri,
            ),
        ).fetchone()

        return (
            self._map_provenance(row)
            if row is not None
            else None
        )

    def find_by_checksum(
        self,
        *,
        conn: sqlite3.Connection,
        checksum_sha256: str,
    ) -> tuple[ProvenanceRecord, ...]:
        rows = conn.execute(
            """
            SELECT
                candidate_id,
                provider_id,
                source_uri,
                local_path,
                filename,
                checksum_sha256,
                first_seen_at,
                last_seen_at,
                sighting_count,
                last_action,
                last_decision_fingerprint,
                campaign_id
            FROM acquisition_provenance
            WHERE checksum_sha256=?
            ORDER BY provider_id, source_uri
            """,
            (checksum_sha256,),
        ).fetchall()

        return tuple(
            self._map_provenance(row)
            for row in rows
        )

    def list_history(
        self,
        *,
        conn: sqlite3.Connection,
        candidate_id: str,
    ) -> tuple[AdmissionHistoryRecord, ...]:
        rows = conn.execute(
            """
            SELECT
                history_id,
                candidate_id,
                seen_at,
                action,
                decision_fingerprint,
                decision_json,
                campaign_id
            FROM acquisition_admission_history
            WHERE candidate_id=?
            ORDER BY history_id
            """,
            (candidate_id,),
        ).fetchall()

        return tuple(
            AdmissionHistoryRecord(
                history_id=int(row[0]),
                candidate_id=str(row[1]),
                seen_at=str(row[2]),
                action=str(row[3]),
                decision_fingerprint=str(row[4]),
                decision_json=str(row[5]),
                campaign_id=(
                    str(row[6])
                    if row[6] is not None
                    else None
                ),
            )
            for row in rows
        )

    def get_history(
        self,
        *,
        conn: sqlite3.Connection,
        history_id: int,
    ) -> AdmissionHistoryRecord:
        row = conn.execute(
            """
            SELECT
                history_id,
                candidate_id,
                seen_at,
                action,
                decision_fingerprint,
                decision_json,
                campaign_id
            FROM acquisition_admission_history
            WHERE history_id=?
            """,
            (history_id,),
        ).fetchone()

        if row is None:
            raise LookupError(
                f"No admission history row: {history_id}"
            )

        return AdmissionHistoryRecord(
            history_id=int(row[0]),
            candidate_id=str(row[1]),
            seen_at=str(row[2]),
            action=str(row[3]),
            decision_fingerprint=str(row[4]),
            decision_json=str(row[5]),
            campaign_id=(
                str(row[6])
                if row[6] is not None
                else None
            ),
        )

    @staticmethod
    def _map_provenance(
        row: sqlite3.Row | tuple[object, ...],
    ) -> ProvenanceRecord:
        return ProvenanceRecord(
            candidate_id=str(row[0]),
            provider_id=str(row[1]),
            source_uri=str(row[2]),
            local_path=str(row[3]),
            filename=str(row[4]),
            checksum_sha256=str(row[5]),
            first_seen_at=str(row[6]),
            last_seen_at=str(row[7]),
            sighting_count=int(row[8]),
            last_action=str(row[9]),
            last_decision_fingerprint=str(row[10]),
            campaign_id=(
                str(row[11])
                if row[11] is not None
                else None
            ),
        )


__all__ = [
    "ProvenanceRepository",
]

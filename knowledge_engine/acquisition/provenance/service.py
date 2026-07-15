"""
Transaction-neutral provenance orchestration.

The caller owns transaction boundaries.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from knowledge_engine.acquisition.admission.models import (
    AdmissionDecision,
)
from knowledge_engine.acquisition.provenance.models import (
    ProvenanceWriteResult,
    candidate_id_for_decision,
)
from knowledge_engine.acquisition.provenance.repository import (
    ProvenanceRepository,
)
from knowledge_engine.acquisition.provenance.schema import (
    ensure_provenance_schema,
)


class ProvenanceService:
    """Record and retrieve durable acquisition provenance."""

    def __init__(
        self,
        repository: ProvenanceRepository | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else ProvenanceRepository()
        )

    def record_decision(
        self,
        *,
        conn: sqlite3.Connection,
        decision: AdmissionDecision,
        seen_at: str | None = None,
        campaign_id: str | None = None,
    ) -> ProvenanceWriteResult:
        ensure_provenance_schema(conn)

        timestamp = (
            seen_at.strip()
            if seen_at is not None
            else datetime.now(
                timezone.utc
            ).isoformat()
        )

        if not timestamp:
            raise ValueError(
                "seen_at must not be empty"
            )

        candidate = decision.candidate

        candidate_id = candidate_id_for_decision(
            decision
        )

        created = not self.repository.source_exists(
            conn=conn,
            provider_id=candidate.provider_id,
            source_uri=candidate.source_uri,
        )

        self.repository.upsert_sighting(
            conn=conn,
            candidate_id=candidate_id,
            provider_id=candidate.provider_id,
            source_uri=candidate.source_uri,
            local_path=candidate.local_path,
            filename=candidate.filename,
            checksum_sha256=candidate.checksum_sha256,
            seen_at=timestamp,
            action=decision.action.value,
            decision_fingerprint=decision.fingerprint,
            campaign_id=campaign_id,
        )

        history_id = self.repository.append_history(
            conn=conn,
            candidate_id=candidate_id,
            seen_at=timestamp,
            action=decision.action.value,
            decision_fingerprint=decision.fingerprint,
            decision_json=json.dumps(
                decision.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
            ),
            campaign_id=campaign_id,
        )

        record = self.repository.get_by_source(
            conn=conn,
            provider_id=candidate.provider_id,
            source_uri=candidate.source_uri,
        )

        if record is None:
            raise RuntimeError(
                "Provenance upsert did not produce a record"
            )

        history = self.repository.get_history(
            conn=conn,
            history_id=history_id,
        )

        return ProvenanceWriteResult(
            record=record,
            history=history,
            created=created,
        )

    def known_checksums(
        self,
        *,
        conn: sqlite3.Connection,
    ) -> frozenset[str]:
        ensure_provenance_schema(conn)

        rows = conn.execute(
            """
            SELECT DISTINCT checksum_sha256
            FROM acquisition_provenance
            ORDER BY checksum_sha256
            """
        ).fetchall()

        return frozenset(
            str(row[0])
            for row in rows
        )


__all__ = [
    "ProvenanceService",
]

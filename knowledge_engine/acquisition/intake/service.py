"""
Provenance-aware acquisition intake.

This service automatically builds AdmissionContext from durable provenance,
evaluates a SourceCandidate, and records the resulting decision.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

import sqlite3

from knowledge_engine.acquisition.admission import (
    AdmissionContext,
    AdmissionDirector,
    build_default_admission_director,
)
from knowledge_engine.acquisition.intake.models import (
    AcquisitionIntakeResult,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)
from knowledge_engine.acquisition.provenance import (
    ProvenanceService,
    ensure_provenance_schema,
)


class AcquisitionIntakeService:
    """
    Evaluate and persist one candidate using durable acquisition memory.

    The service does not commit or roll back the supplied connection.
    """

    def __init__(
        self,
        *,
        admission_director: AdmissionDirector | None = None,
        provenance_service: ProvenanceService | None = None,
    ):
        self.admission_director = (
            admission_director
            if admission_director is not None
            else build_default_admission_director()
        )

        self.provenance_service = (
            provenance_service
            if provenance_service is not None
            else ProvenanceService()
        )

    def evaluate_and_record(
        self,
        *,
        conn: sqlite3.Connection,
        candidate: SourceCandidate,
        campaign_id: str | None = None,
        seen_at: str | None = None,
    ) -> AcquisitionIntakeResult:
        """
        Evaluate one candidate against durable checksums and record the result.

        The known-checksum snapshot is taken before recording the current
        candidate. Therefore, a never-before-seen checksum is accepted by the
        duplicate policy on first sighting and ignored on later sightings.
        """

        if not isinstance(conn, sqlite3.Connection):
            raise TypeError(
                "conn must be a sqlite3.Connection"
            )

        if not isinstance(candidate, SourceCandidate):
            raise TypeError(
                "candidate must be a SourceCandidate"
            )

        normalized_campaign = (
            campaign_id.strip()
            if campaign_id is not None
            else None
        )

        if normalized_campaign == "":
            normalized_campaign = None

        ensure_provenance_schema(conn)

        known_checksums = (
            self.provenance_service.known_checksums(
                conn=conn
            )
        )

        context = AdmissionContext(
            known_checksums=known_checksums,
            campaign_id=normalized_campaign,
            metadata={
                "context_source": "provenance",
                "known_checksum_count": len(
                    known_checksums
                ),
            },
        )

        decision = (
            self.admission_director.evaluate_candidate(
                candidate=candidate,
                context=context,
            )
        )

        provenance = (
            self.provenance_service.record_decision(
                conn=conn,
                decision=decision,
                seen_at=seen_at,
                campaign_id=normalized_campaign,
            )
        )

        return AcquisitionIntakeResult(
            decision=decision,
            provenance=provenance,
            known_checksum_count=len(
                known_checksums
            ),
        )


__all__ = [
    "AcquisitionIntakeService",
]

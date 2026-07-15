"""
Durable acquisition-mission construction.

The service converts provenance-backed intake results into one mission.
It does not execute items or invoke assimilation.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone

from knowledge_engine.acquisition.intake.models import (
    AcquisitionIntakeResult,
)
from knowledge_engine.acquisition.missions.identity import (
    build_acquisition_mission_id,
)
from knowledge_engine.acquisition.missions.models import (
    AcquisitionMissionBuildResult,
    AcquisitionMissionItemState,
    AcquisitionMissionState,
)
from knowledge_engine.acquisition.missions.repository import (
    AcquisitionMissionRepository,
)
from knowledge_engine.acquisition.missions.schema import (
    ensure_acquisition_mission_schema,
)


ACTION_TO_ITEM_STATE = {
    "accept": AcquisitionMissionItemState.ACCEPTED,
    "review": AcquisitionMissionItemState.REVIEW,
    "ignore": AcquisitionMissionItemState.IGNORED,
    "reject": AcquisitionMissionItemState.REJECTED,
}


class AcquisitionMissionService:
    """Construct durable, deterministic acquisition missions."""

    def __init__(
        self,
        repository: AcquisitionMissionRepository | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else AcquisitionMissionRepository()
        )

    def create_mission(
        self,
        *,
        conn: sqlite3.Connection,
        request_id: str,
        provider_id: str,
        intake_results: Iterable[AcquisitionIntakeResult],
        campaign_id: str | None = None,
        created_at: str | None = None,
    ) -> AcquisitionMissionBuildResult:
        """Create or resolve one mission from intake results."""

        if not isinstance(conn, sqlite3.Connection):
            raise TypeError(
                "conn must be a sqlite3.Connection"
            )

        normalized_request = request_id.strip()
        normalized_provider = provider_id.strip()
        normalized_campaign = (
            campaign_id.strip()
            if campaign_id is not None
            else None
        )

        if not normalized_request:
            raise ValueError(
                "request_id must not be empty"
            )

        if not normalized_provider:
            raise ValueError(
                "provider_id must not be empty"
            )

        if normalized_campaign == "":
            normalized_campaign = None

        timestamp = (
            created_at.strip()
            if created_at is not None
            else datetime.now(
                timezone.utc
            ).isoformat()
        )

        if not timestamp:
            raise ValueError(
                "created_at must not be empty"
            )

        results = tuple(
            sorted(
                intake_results,
                key=lambda result: (
                    result.decision.candidate.local_path,
                    result.candidate_id,
                ),
            )
        )

        candidate_ids = tuple(
            result.candidate_id
            for result in results
        )

        if len(candidate_ids) != len(
            set(candidate_ids)
        ):
            raise ValueError(
                "intake_results contain duplicate candidate IDs"
            )

        for result in results:
            if (
                result.decision.candidate.provider_id
                != normalized_provider
            ):
                raise ValueError(
                    "all mission items must use the mission provider"
                )

        mission_id = build_acquisition_mission_id(
            request_id=normalized_request,
            provider_id=normalized_provider,
            campaign_id=normalized_campaign,
        )

        ensure_acquisition_mission_schema(conn)

        if self.repository.mission_exists(
            conn=conn,
            mission_id=mission_id,
        ):
            return AcquisitionMissionBuildResult(
                mission=self.repository.get_mission(
                    conn=conn,
                    mission_id=mission_id,
                ),
                items=self.repository.list_items(
                    conn=conn,
                    mission_id=mission_id,
                ),
                created=False,
            )

        states = tuple(
            ACTION_TO_ITEM_STATE[result.action]
            for result in results
        )

        accepted_count = states.count(
            AcquisitionMissionItemState.ACCEPTED
        )
        review_count = states.count(
            AcquisitionMissionItemState.REVIEW
        )
        ignored_count = states.count(
            AcquisitionMissionItemState.IGNORED
        )
        rejected_count = states.count(
            AcquisitionMissionItemState.REJECTED
        )

        mission_state = (
            AcquisitionMissionState.READY
            if accepted_count > 0
            else AcquisitionMissionState.COMPLETED
        )

        self.repository.insert_mission(
            conn=conn,
            mission_id=mission_id,
            request_id=normalized_request,
            provider_id=normalized_provider,
            campaign_id=normalized_campaign,
            mission_state=mission_state.value,
            timestamp=timestamp,
            item_count=len(results),
            accepted_count=accepted_count,
            review_count=review_count,
            ignored_count=ignored_count,
            rejected_count=rejected_count,
        )

        for item_order, result in enumerate(results):
            candidate = result.decision.candidate

            self.repository.insert_item(
                conn=conn,
                mission_id=mission_id,
                item_order=item_order,
                candidate_id=result.candidate_id,
                provider_id=candidate.provider_id,
                source_uri=candidate.source_uri,
                local_path=candidate.local_path,
                checksum_sha256=candidate.checksum_sha256,
                item_state=ACTION_TO_ITEM_STATE[
                    result.action
                ].value,
                decision_fingerprint=(
                    result.decision.fingerprint
                ),
                timestamp=timestamp,
            )

        return AcquisitionMissionBuildResult(
            mission=self.repository.get_mission(
                conn=conn,
                mission_id=mission_id,
            ),
            items=self.repository.list_items(
                conn=conn,
                mission_id=mission_id,
            ),
            created=True,
        )


__all__ = [
    "AcquisitionMissionService",
]

"""
Controlled acquisition-to-assimilation handoff preparation.

Only accepted acquisition mission items may create handoff requests.
Review, ignored, and rejected items are excluded by construction.

The service does not dispatch work into Phase VI yet.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from knowledge_engine.acquisition.handoff.identity import (
    build_assimilation_handoff_id,
)
from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffBuildResult,
)
from knowledge_engine.acquisition.handoff.repository import (
    AssimilationHandoffRepository,
)
from knowledge_engine.acquisition.handoff.schema import (
    ensure_assimilation_handoff_schema,
)
from knowledge_engine.acquisition.missions import (
    AcquisitionMissionItemState,
    AcquisitionMissionRepository,
    AcquisitionMissionState,
    ensure_acquisition_mission_schema,
)


class AssimilationHandoffService:
    """Prepare accepted acquisition mission items for assimilation."""

    def __init__(
        self,
        *,
        handoff_repository: (
            AssimilationHandoffRepository | None
        ) = None,
        mission_repository: (
            AcquisitionMissionRepository | None
        ) = None,
    ):
        self.handoff_repository = (
            handoff_repository
            if handoff_repository is not None
            else AssimilationHandoffRepository()
        )

        self.mission_repository = (
            mission_repository
            if mission_repository is not None
            else AcquisitionMissionRepository()
        )

    def prepare_mission(
        self,
        *,
        conn: sqlite3.Connection,
        mission_id: str,
        created_at: str | None = None,
    ) -> AssimilationHandoffBuildResult:
        """Create handoff requests for accepted mission items only."""

        if not isinstance(conn, sqlite3.Connection):
            raise TypeError(
                "conn must be a sqlite3.Connection"
            )

        normalized_mission_id = mission_id.strip()

        if not normalized_mission_id:
            raise ValueError(
                "mission_id must not be empty"
            )

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

        ensure_acquisition_mission_schema(conn)
        ensure_assimilation_handoff_schema(conn)

        mission = self.mission_repository.get_mission(
            conn=conn,
            mission_id=normalized_mission_id,
        )

        if mission.mission_state not in {
            AcquisitionMissionState.READY,
            AcquisitionMissionState.COMPLETED,
        }:
            raise ValueError(
                "Only ready or completed acquisition missions "
                "may be prepared for handoff"
            )

        mission_items = (
            self.mission_repository.list_items(
                conn=conn,
                mission_id=normalized_mission_id,
            )
        )

        accepted_items = tuple(
            item
            for item in mission_items
            if item.item_state
            is AcquisitionMissionItemState.ACCEPTED
        )

        excluded_count = (
            len(mission_items)
            - len(accepted_items)
        )

        created_count = 0
        existing_count = 0

        for item in accepted_items:
            if self.handoff_repository.handoff_exists(
                conn=conn,
                mission_id=normalized_mission_id,
                mission_item_id=item.item_id,
            ):
                existing_count += 1
                continue

            handoff_id = build_assimilation_handoff_id(
                mission_id=normalized_mission_id,
                candidate_id=item.candidate_id,
            )

            self.handoff_repository.insert_handoff(
                conn=conn,
                handoff_id=handoff_id,
                mission_id=normalized_mission_id,
                mission_item_id=item.item_id,
                candidate_id=item.candidate_id,
                provider_id=item.provider_id,
                source_uri=item.source_uri,
                local_path=item.local_path,
                checksum_sha256=item.checksum_sha256,
                decision_fingerprint=(
                    item.decision_fingerprint
                ),
                timestamp=timestamp,
            )

            created_count += 1

        handoffs = (
            self.handoff_repository.list_for_mission(
                conn=conn,
                mission_id=normalized_mission_id,
            )
        )

        if any(
            handoff.mission_item_id
            not in {
                item.item_id
                for item in accepted_items
            }
            for handoff in handoffs
        ):
            raise RuntimeError(
                "Non-accepted mission item crossed the "
                "assimilation handoff boundary"
            )

        return AssimilationHandoffBuildResult(
            mission_id=normalized_mission_id,
            handoffs=handoffs,
            created_count=created_count,
            existing_count=existing_count,
            excluded_count=excluded_count,
        )


__all__ = [
    "AssimilationHandoffService",
]

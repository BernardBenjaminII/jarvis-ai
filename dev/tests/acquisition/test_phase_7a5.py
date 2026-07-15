"""
Phase VII-A5 durable acquisition-mission verification.

All persistence uses an in-memory SQLite database.
"""

from __future__ import annotations

import hashlib
import sqlite3

from knowledge_engine.acquisition.intake import (
    AcquisitionIntakeResult,
    AcquisitionIntakeService,
)
from knowledge_engine.acquisition.missions import (
    AcquisitionMissionItemState,
    AcquisitionMissionService,
    AcquisitionMissionState,
    ensure_acquisition_mission_schema,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


def make_candidate(
    *,
    filename: str,
    content: bytes,
    extension: str = ".txt",
    candidate_type: str = "document",
) -> SourceCandidate:
    return SourceCandidate(
        provider_id="filesystem",
        source_uri=f"file:///tmp/{filename}",
        local_path=f"/tmp/{filename}",
        filename=filename,
        extension=extension,
        media_type="application/octet-stream",
        candidate_type=candidate_type,
        size_bytes=len(content),
        checksum_sha256=hashlib.sha256(
            content
        ).hexdigest(),
    )


def build_intake_results(
    conn: sqlite3.Connection,
) -> tuple[AcquisitionIntakeResult, ...]:
    intake = AcquisitionIntakeService()

    accepted = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="accepted.txt",
            content=b"accepted content",
        ),
        seen_at="2026-07-15T19:00:00+00:00",
    )

    ignored = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="mirror.txt",
            content=b"accepted content",
        ),
        seen_at="2026-07-15T19:01:00+00:00",
    )

    review = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="review.xyz",
            extension=".xyz",
            candidate_type="generic_file",
            content=b"review content",
        ),
        seen_at="2026-07-15T19:02:00+00:00",
    )

    rejected = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="rejected.exe",
            extension=".exe",
            candidate_type="generic_file",
            content=b"MZ rejected content",
        ),
        seen_at="2026-07-15T19:03:00+00:00",
    )

    return (
        rejected,
        ignored,
        accepted,
        review,
    )


def verify_schema(
    conn: sqlite3.Connection,
) -> None:
    ensure_acquisition_mission_schema(conn)
    ensure_acquisition_mission_schema(conn)

    tables = {
        str(row[0])
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        )
    }

    assert "acquisition_missions" in tables
    assert "acquisition_mission_items" in tables


def verify_mission_construction(
    conn: sqlite3.Connection,
) -> str:
    service = AcquisitionMissionService()

    result = service.create_mission(
        conn=conn,
        request_id="phase-7a5-request",
        provider_id="filesystem",
        intake_results=build_intake_results(conn),
        campaign_id="phase-7a5",
        created_at="2026-07-15T20:00:00+00:00",
    )

    assert result.created is True

    mission = result.mission

    assert mission.mission_state is (
        AcquisitionMissionState.READY
    )
    assert mission.item_count == 4
    assert mission.accepted_count == 1
    assert mission.review_count == 1
    assert mission.ignored_count == 1
    assert mission.rejected_count == 1

    assert tuple(
        item.item_order
        for item in result.items
    ) == (
        0,
        1,
        2,
        3,
    )

    assert tuple(
        item.local_path
        for item in result.items
    ) == tuple(
        sorted(
            item.local_path
            for item in result.items
        )
    )

    assert {
        item.item_state
        for item in result.items
    } == {
        AcquisitionMissionItemState.ACCEPTED,
        AcquisitionMissionItemState.REVIEW,
        AcquisitionMissionItemState.IGNORED,
        AcquisitionMissionItemState.REJECTED,
    }

    return mission.mission_id


def verify_idempotency(
    conn: sqlite3.Connection,
    mission_id: str,
) -> None:
    service = AcquisitionMissionService()

    existing_items = service.repository.list_items(
        conn=conn,
        mission_id=mission_id,
    )

    result = service.create_mission(
        conn=conn,
        request_id="phase-7a5-request",
        provider_id="filesystem",
        intake_results=(),
        campaign_id="phase-7a5",
        created_at="2026-07-15T21:00:00+00:00",
    )

    assert result.created is False
    assert result.mission.mission_id == mission_id
    assert result.items == existing_items


def verify_empty_mission(
    conn: sqlite3.Connection,
) -> None:
    result = AcquisitionMissionService().create_mission(
        conn=conn,
        request_id="empty-request",
        provider_id="filesystem",
        intake_results=(),
        created_at="2026-07-15T22:00:00+00:00",
    )

    assert result.created is True
    assert result.mission.item_count == 0
    assert result.mission.mission_state is (
        AcquisitionMissionState.COMPLETED
    )


def verify_rollback() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    service = AcquisitionMissionService()

    try:
        conn.execute("BEGIN")

        result = service.create_mission(
            conn=conn,
            request_id="rollback-request",
            provider_id="filesystem",
            intake_results=(),
            created_at="2026-07-15T23:00:00+00:00",
        )

        mission_id = result.mission.mission_id

        conn.rollback()

        try:
            service.repository.get_mission(
                conn=conn,
                mission_id=mission_id,
            )
        except LookupError:
            pass
        else:
            raise AssertionError(
                "Rolled-back mission still exists"
            )
    finally:
        conn.close()


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.execute("BEGIN")

        verify_schema(conn)

        mission_id = verify_mission_construction(
            conn
        )

        verify_idempotency(
            conn,
            mission_id,
        )

        verify_empty_mission(conn)

        conn.commit()
    finally:
        conn.close()

    verify_rollback()

    print("[PASS] Mission schema idempotency")
    print("[PASS] Deterministic mission identity")
    print("[PASS] Durable mission construction")
    print("[PASS] Complete outcome accounting")
    print("[PASS] Deterministic mission-item ordering")
    print("[PASS] Mission creation idempotency")
    print("[PASS] Empty-mission completion")
    print("[PASS] Caller-owned transaction rollback")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A5 acquisition missions verified")


if __name__ == "__main__":
    main()

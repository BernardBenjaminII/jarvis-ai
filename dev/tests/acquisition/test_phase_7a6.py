"""
Phase VII-A6 controlled assimilation-handoff verification.

All persistence uses an in-memory SQLite database.
No Phase VI assimilation execution occurs.
"""

from __future__ import annotations

import hashlib
import sqlite3

from knowledge_engine.acquisition.handoff import (
    AssimilationHandoffService,
    AssimilationHandoffState,
    ensure_assimilation_handoff_schema,
)
from knowledge_engine.acquisition.intake import (
    AcquisitionIntakeService,
)
from knowledge_engine.acquisition.missions import (
    AcquisitionMissionService,
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


def create_mission(
    conn: sqlite3.Connection,
) -> str:
    intake = AcquisitionIntakeService()

    accepted = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="accepted.txt",
            content=b"unique accepted content",
        ),
        seen_at="2026-07-15T20:00:00+00:00",
    )

    ignored = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="mirror.txt",
            content=b"unique accepted content",
        ),
        seen_at="2026-07-15T20:01:00+00:00",
    )

    review = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="review.xyz",
            content=b"review content",
            extension=".xyz",
            candidate_type="generic_file",
        ),
        seen_at="2026-07-15T20:02:00+00:00",
    )

    rejected = intake.evaluate_and_record(
        conn=conn,
        candidate=make_candidate(
            filename="rejected.exe",
            content=b"MZ rejected",
            extension=".exe",
            candidate_type="generic_file",
        ),
        seen_at="2026-07-15T20:03:00+00:00",
    )

    mission = AcquisitionMissionService().create_mission(
        conn=conn,
        request_id="phase-7a6-request",
        provider_id="filesystem",
        intake_results=(
            rejected,
            ignored,
            review,
            accepted,
        ),
        campaign_id="phase-7a6",
        created_at="2026-07-15T21:00:00+00:00",
    )

    assert mission.mission.accepted_count == 1
    assert mission.mission.review_count == 1
    assert mission.mission.ignored_count == 1
    assert mission.mission.rejected_count == 1

    return mission.mission.mission_id


def verify_schema(
    conn: sqlite3.Connection,
) -> None:
    ensure_assimilation_handoff_schema(conn)
    ensure_assimilation_handoff_schema(conn)

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

    assert (
        "acquisition_assimilation_handoffs"
        in tables
    )


def verify_accepted_only_boundary(
    conn: sqlite3.Connection,
    mission_id: str,
) -> None:
    service = AssimilationHandoffService()

    result = service.prepare_mission(
        conn=conn,
        mission_id=mission_id,
        created_at="2026-07-15T22:00:00+00:00",
    )

    assert result.created_count == 1
    assert result.existing_count == 0
    assert result.excluded_count == 3
    assert result.handoff_count == 1

    handoff = result.handoffs[0]

    assert handoff.handoff_state is (
        AssimilationHandoffState.QUEUED
    )
    assert handoff.local_path.endswith(
        "/accepted.txt"
    )
    assert handoff.dispatch_attempt_count == 0
    assert handoff.assimilation_reference is None
    assert handoff.last_error is None


def verify_idempotency(
    conn: sqlite3.Connection,
    mission_id: str,
) -> None:
    result = AssimilationHandoffService().prepare_mission(
        conn=conn,
        mission_id=mission_id,
        created_at="2026-07-15T23:00:00+00:00",
    )

    assert result.created_count == 0
    assert result.existing_count == 1
    assert result.excluded_count == 3
    assert result.handoff_count == 1


def verify_queued_inventory(
    conn: sqlite3.Connection,
) -> None:
    service = AssimilationHandoffService()

    queued = service.handoff_repository.list_queued(
        conn=conn,
        limit=10,
    )

    assert len(queued) == 1
    assert queued[0].handoff_state is (
        AssimilationHandoffState.QUEUED
    )


def verify_empty_completed_mission(
    conn: sqlite3.Connection,
) -> None:
    mission = AcquisitionMissionService().create_mission(
        conn=conn,
        request_id="empty-handoff-request",
        provider_id="filesystem",
        intake_results=(),
        created_at="2026-07-16T00:00:00+00:00",
    )

    result = AssimilationHandoffService().prepare_mission(
        conn=conn,
        mission_id=mission.mission.mission_id,
        created_at="2026-07-16T00:01:00+00:00",
    )

    assert result.created_count == 0
    assert result.existing_count == 0
    assert result.excluded_count == 0
    assert result.handoff_count == 0


def verify_rollback() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.execute("BEGIN")

        mission_id = create_mission(conn)

        result = AssimilationHandoffService().prepare_mission(
            conn=conn,
            mission_id=mission_id,
            created_at="2026-07-16T01:00:00+00:00",
        )

        handoff_id = result.handoffs[0].handoff_id

        conn.rollback()

        try:
            (
                AssimilationHandoffService()
                .handoff_repository
                .get_handoff(
                    conn=conn,
                    handoff_id=handoff_id,
                )
            )
        except LookupError:
            pass
        else:
            raise AssertionError(
                "Rolled-back handoff still exists"
            )
    finally:
        conn.close()


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.execute("BEGIN")

        mission_id = create_mission(conn)

        verify_schema(conn)

        verify_accepted_only_boundary(
            conn,
            mission_id,
        )

        verify_idempotency(
            conn,
            mission_id,
        )

        verify_queued_inventory(conn)

        verify_empty_completed_mission(conn)

        conn.commit()
    finally:
        conn.close()

    verify_rollback()

    print("[PASS] Handoff schema idempotency")
    print("[PASS] Accepted-item-only boundary")
    print("[PASS] Review-item exclusion")
    print("[PASS] Ignored-item exclusion")
    print("[PASS] Rejected-item exclusion")
    print("[PASS] Deterministic handoff identity")
    print("[PASS] Handoff creation idempotency")
    print("[PASS] Queued handoff inventory")
    print("[PASS] Empty completed mission handling")
    print("[PASS] Caller-owned transaction rollback")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A6 assimilation handoff verified")


if __name__ == "__main__":
    main()

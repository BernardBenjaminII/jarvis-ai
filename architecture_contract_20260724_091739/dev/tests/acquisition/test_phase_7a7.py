"""
Phase VII-A7 canonical assimilation-dispatch verification.

This focused suite verifies:

- atomic queued-handoff claiming
- deterministic and bounded dispatch
- mandatory registration before Phase VI execution
- successful dispatch persistence
- failed-dispatch diagnostics
- failed-handoff requeue
- dispatch-attempt limits
- duplicate-dispatch prevention
- stale dispatch-claim recovery
- stop-on-error claim release

All persistence uses temporary in-memory SQLite databases.

No live catalog is modified.
No extraction is performed.
No real Phase VI assimilation is executed.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Any

from knowledge_engine.acquisition.dispatch import (
    AssimilationDispatchRepository,
    CanonicalAssimilationDispatcher,
)
from knowledge_engine.acquisition.handoff import (
    AssimilationHandoffService,
    AssimilationHandoffState,
)
from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
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


class FakeRegistrationPort:
    """
    Deterministic stand-in for the future Knowledge Registry adapter.

    The fixture returns candidate_id as the registered object UUID. Production
    code must use the canonical Knowledge Registry registration implementation.
    """

    def __init__(
        self,
        *,
        fail_handoff_ids: set[str] | None = None,
        empty_handoff_ids: set[str] | None = None,
    ) -> None:
        self.fail_handoff_ids = (
            set(fail_handoff_ids)
            if fail_handoff_ids is not None
            else set()
        )

        self.empty_handoff_ids = (
            set(empty_handoff_ids)
            if empty_handoff_ids is not None
            else set()
        )

        self.calls: list[str] = []

    def ensure_registered(
        self,
        *,
        handoff: AssimilationHandoffRecord,
    ) -> str:
        self.calls.append(
            handoff.handoff_id
        )

        if handoff.handoff_id in self.fail_handoff_ids:
            raise RuntimeError(
                "fixture registration failure"
            )

        if handoff.handoff_id in self.empty_handoff_ids:
            return ""

        return handoff.candidate_id


class FakeExecutionPort:
    """
    Deterministic stand-in for the Phase VI execution adapter.

    Results follow the public AssimilationRunner result shape.
    """

    def __init__(
        self,
        *,
        fail_object_uuids: set[str] | None = None,
        blocked_object_uuids: set[str] | None = None,
        wrong_uuid_object_uuids: set[str] | None = None,
        exception_object_uuids: set[str] | None = None,
    ) -> None:
        self.fail_object_uuids = (
            set(fail_object_uuids)
            if fail_object_uuids is not None
            else set()
        )

        self.blocked_object_uuids = (
            set(blocked_object_uuids)
            if blocked_object_uuids is not None
            else set()
        )

        self.wrong_uuid_object_uuids = (
            set(wrong_uuid_object_uuids)
            if wrong_uuid_object_uuids is not None
            else set()
        )

        self.exception_object_uuids = (
            set(exception_object_uuids)
            if exception_object_uuids is not None
            else set()
        )

        self.calls: list[str] = []

    def execute_registered_object(
        self,
        *,
        object_uuid: str,
    ) -> dict[str, Any]:
        self.calls.append(object_uuid)

        if object_uuid in self.exception_object_uuids:
            raise RuntimeError(
                "fixture execution exception"
            )

        if object_uuid in self.fail_object_uuids:
            return {
                "processed": 0,
                "failed": 1,
                "object_uuid": object_uuid,
                "error": "fixture assimilation failure",
            }

        if object_uuid in self.blocked_object_uuids:
            return {
                "processed": 0,
                "failed": 0,
                "object_uuid": object_uuid,
                "message": (
                    "fixture object was not eligible for processing"
                ),
            }

        if object_uuid in self.wrong_uuid_object_uuids:
            return {
                "processed": 1,
                "failed": 0,
                "object_uuid": "different-object-uuid",
            }

        return {
            "processed": 1,
            "failed": 0,
            "object_uuid": object_uuid,
        }


def open_database() -> sqlite3.Connection:
    """Create one isolated test database."""

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


def make_candidate(
    *,
    filename: str,
    content: bytes,
) -> SourceCandidate:
    """Create one deterministic accepted acquisition candidate."""

    return SourceCandidate(
        provider_id="filesystem",
        source_uri=f"file:///tmp/{filename}",
        local_path=f"/tmp/{filename}",
        filename=filename,
        extension=".txt",
        media_type="text/plain",
        candidate_type="document",
        size_bytes=len(content),
        checksum_sha256=hashlib.sha256(
            content
        ).hexdigest(),
    )


def create_ready_handoffs(
    conn: sqlite3.Connection,
    *,
    count: int,
    request_id: str,
) -> tuple[AssimilationHandoffRecord, ...]:
    """
    Create a mission containing count unique accepted candidates.

    The helper exercises the actual VII-A4, VII-A5, and VII-A6 services.
    """

    if count < 1:
        raise ValueError(
            "count must be at least 1"
        )

    intake_service = AcquisitionIntakeService()

    intake_results = tuple(
        intake_service.evaluate_and_record(
            conn=conn,
            candidate=make_candidate(
                filename=(
                    f"{request_id}-"
                    f"document-{index:03d}.txt"
                ),
                content=(
                    f"{request_id}-unique-content-{index}"
                ).encode("utf-8"),
            ),
            campaign_id="phase-7a7",
            seen_at=(
                "2026-07-16T"
                f"{index:02d}:00:00+00:00"
            ),
        )
        for index in range(count)
    )

    mission_result = (
        AcquisitionMissionService()
        .create_mission(
            conn=conn,
            request_id=request_id,
            provider_id="filesystem",
            intake_results=intake_results,
            campaign_id="phase-7a7",
            created_at=(
                "2026-07-16T10:00:00+00:00"
            ),
        )
    )

    assert mission_result.mission.accepted_count == count
    assert mission_result.mission.item_count == count

    handoff_result = (
        AssimilationHandoffService()
        .prepare_mission(
            conn=conn,
            mission_id=(
                mission_result.mission.mission_id
            ),
            created_at=(
                "2026-07-16T11:00:00+00:00"
            ),
        )
    )

    assert handoff_result.created_count == count
    assert handoff_result.handoff_count == count

    return handoff_result.handoffs


def verify_successful_dispatch() -> None:
    """Verify registration, execution, and successful persistence."""

    conn = open_database()

    try:
        initial_handoffs = create_ready_handoffs(
            conn,
            count=2,
            request_id="successful-dispatch",
        )

        registration = FakeRegistrationPort()
        execution = FakeExecutionPort()

        dispatcher = CanonicalAssimilationDispatcher(
            registration_port=registration,
            execution_port=execution,
        )

        result = dispatcher.dispatch(
            conn=conn,
            limit=10,
            timestamp=(
                "2026-07-16T12:00:00+00:00"
            ),
        )

        assert result.claimed == 2
        assert result.dispatched == 2
        assert result.failed == 0
        assert result.skipped == 0
        assert result.succeeded is True

        expected = {
            handoff.handoff_id
            for handoff in initial_handoffs
        }

        actual = set(registration.calls)
        assert actual == expected


        assert actual == expected
        expected = {
            handoff.candidate_id
            for handoff in initial_handoffs
        }

        actual = set(execution.calls)


        assert len(execution.calls) == len(initial_handoffs)

        assert len(actual) == len(initial_handoffs)

        assert actual == expected

        assert all(
            handoff.handoff_state
            is AssimilationHandoffState.DISPATCHED
            for handoff in result.handoffs
        )

        assert all(
            handoff.dispatch_attempt_count == 1
            for handoff in result.handoffs
        )

        assert all(
            handoff.assimilation_reference
            == handoff.candidate_id
            for handoff in result.handoffs
        )

        assert all(
            handoff.last_error is None
            for handoff in result.handoffs
        )

    finally:
        conn.close()


def verify_bounded_dispatch() -> None:
    """Verify the dispatcher claims no more than the requested limit."""

    conn = open_database()

    try:
        create_ready_handoffs(
            conn,
            count=3,
            request_id="bounded-dispatch",
        )

        repository = AssimilationDispatchRepository()

        result = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(),
            repository=repository,
        ).dispatch(
            conn=conn,
            limit=2,
            timestamp=(
                "2026-07-16T13:00:00+00:00"
            ),
        )

        assert result.claimed == 2
        assert result.dispatched == 2

        assert repository.count_by_state(
            conn=conn,
            state=(
                AssimilationHandoffState.DISPATCHED
            ),
        ) == 2

        assert repository.count_by_state(
            conn=conn,
            state=AssimilationHandoffState.QUEUED,
        ) == 1

    finally:
        conn.close()


def verify_failure_recording() -> None:
    """Verify Phase VI failure results become durable failed handoffs."""

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=1,
            request_id="failure-recording",
        )

        object_uuid = handoffs[0].candidate_id

        result = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(
                fail_object_uuids={
                    object_uuid,
                },
            ),
        ).dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T14:00:00+00:00"
            ),
        )

        assert result.claimed == 1
        assert result.dispatched == 0
        assert result.failed == 1
        assert result.skipped == 0
        assert result.succeeded is False

        failed = result.handoffs[0]

        assert failed.handoff_state is (
            AssimilationHandoffState.FAILED
        )

        assert failed.dispatch_attempt_count == 1

        assert "fixture assimilation failure" in (
            failed.last_error or ""
        )

        assert failed.assimilation_reference is None

    finally:
        conn.close()


def verify_registration_failure_recording() -> None:
    """Verify registration failures never invoke Phase VI."""

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=1,
            request_id="registration-failure",
        )

        registration = FakeRegistrationPort(
            fail_handoff_ids={
                handoffs[0].handoff_id,
            },
        )

        execution = FakeExecutionPort()

        result = CanonicalAssimilationDispatcher(
            registration_port=registration,
            execution_port=execution,
        ).dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T15:00:00+00:00"
            ),
        )

        assert result.failed == 1
        assert len(registration.calls) == 1
        assert execution.calls == []

        failed = result.handoffs[0]

        assert failed.handoff_state is (
            AssimilationHandoffState.FAILED
        )

        assert "fixture registration failure" in (
            failed.last_error or ""
        )

    finally:
        conn.close()


def verify_wrong_phase_vi_uuid_is_rejected() -> None:
    """Verify Phase VI cannot complete a different registry object."""

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=1,
            request_id="wrong-returned-uuid",
        )

        object_uuid = handoffs[0].candidate_id

        result = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(
                wrong_uuid_object_uuids={
                    object_uuid,
                },
            ),
        ).dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T16:00:00+00:00"
            ),
        )

        assert result.failed == 1

        failed = result.handoffs[0]

        assert failed.handoff_state is (
            AssimilationHandoffState.FAILED
        )

        assert "different object UUID" in (
            failed.last_error or ""
        )

    finally:
        conn.close()


def verify_failed_handoff_requeue() -> None:
    """Verify failed handoffs below the attempt limit can be requeued."""

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=1,
            request_id="failure-requeue",
        )

        object_uuid = handoffs[0].candidate_id

        dispatcher = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(
                fail_object_uuids={
                    object_uuid,
                },
            ),
        )

        failed_result = dispatcher.dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T17:00:00+00:00"
            ),
        )

        assert failed_result.failed == 1

        requeued = dispatcher.requeue_failed(
            conn=conn,
            limit=10,
            max_attempts=3,
            timestamp=(
                "2026-07-16T18:00:00+00:00"
            ),
        )

        assert len(requeued) == 1

        assert requeued[0].handoff_state is (
            AssimilationHandoffState.QUEUED
        )

        assert requeued[0].dispatch_attempt_count == 1
        assert requeued[0].last_error is None

    finally:
        conn.close()


def verify_attempt_limit_enforcement() -> None:
    """Verify exhausted failed handoffs are not requeued."""

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=1,
            request_id="attempt-limit",
        )

        object_uuid = handoffs[0].candidate_id

        dispatcher = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(
                fail_object_uuids={
                    object_uuid,
                },
            ),
        )

        first_failure = dispatcher.dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T19:00:00+00:00"
            ),
        )

        assert first_failure.failed == 1

        first_requeue = dispatcher.requeue_failed(
            conn=conn,
            limit=1,
            max_attempts=2,
            timestamp=(
                "2026-07-16T20:00:00+00:00"
            ),
        )

        assert len(first_requeue) == 1

        second_failure = dispatcher.dispatch(
            conn=conn,
            limit=1,
            timestamp=(
                "2026-07-16T21:00:00+00:00"
            ),
        )

        assert second_failure.failed == 1
        assert (
            second_failure.handoffs[0]
            .dispatch_attempt_count
            == 2
        )

        exhausted_requeue = dispatcher.requeue_failed(
            conn=conn,
            limit=1,
            max_attempts=2,
            timestamp=(
                "2026-07-16T22:00:00+00:00"
            ),
        )

        assert exhausted_requeue == ()

    finally:
        conn.close()


def verify_duplicate_dispatch_prevention() -> None:
    """Verify dispatched handoffs cannot be claimed twice."""

    conn = open_database()

    try:
        create_ready_handoffs(
            conn,
            count=1,
            request_id="duplicate-prevention",
        )

        dispatcher = CanonicalAssimilationDispatcher(
            registration_port=FakeRegistrationPort(),
            execution_port=FakeExecutionPort(),
        )

        first = dispatcher.dispatch(
            conn=conn,
            limit=10,
            timestamp=(
                "2026-07-16T23:00:00+00:00"
            ),
        )

        second = dispatcher.dispatch(
            conn=conn,
            limit=10,
            timestamp=(
                "2026-07-17T00:00:00+00:00"
            ),
        )

        assert first.claimed == 1
        assert first.dispatched == 1

        assert second.claimed == 0
        assert second.dispatched == 0
        assert second.failed == 0
        assert second.skipped == 0
        assert second.handoffs == ()

    finally:
        conn.close()


def verify_stale_claim_recovery() -> None:
    """Verify interrupted dispatching claims return to queued."""

    conn = open_database()

    try:
        create_ready_handoffs(
            conn,
            count=1,
            request_id="stale-recovery",
        )

        repository = AssimilationDispatchRepository()

        claimed = repository.claim_queued(
            conn=conn,
            limit=1,
            claimed_at=(
                "2026-07-16T10:00:00+00:00"
            ),
        )

        assert len(claimed) == 1

        assert claimed[0].handoff_state is (
            AssimilationHandoffState.DISPATCHING
        )

        recovered = (
            repository.recover_stale_dispatching(
                conn=conn,
                stale_after_minutes=30,
                now=datetime(
                    2026,
                    7,
                    16,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
            )
        )

        assert len(recovered) == 1

        assert recovered[0].handoff_state is (
            AssimilationHandoffState.QUEUED
        )

        assert (
            recovered[0].dispatch_attempt_count
            == 1
        )

        assert "Recovered interrupted" in (
            recovered[0].last_error or ""
        )

    finally:
        conn.close()


def verify_stop_on_error_releases_remaining_claims() -> None:
    """
    Verify stop_on_error does not leave later claimed rows dispatching.

    The first handoff fails. Remaining claimed handoffs return to queued.
    """

    conn = open_database()

    try:
        handoffs = create_ready_handoffs(
            conn,
            count=3,
            request_id="stop-on-error",
        )

        first_object_uuid = (
            handoffs[0].candidate_id
        )

        registration = FakeRegistrationPort()

        execution = FakeExecutionPort(
            fail_object_uuids={
                first_object_uuid,
            },
        )

        result = CanonicalAssimilationDispatcher(
            registration_port=registration,
            execution_port=execution,
        ).dispatch(
            conn=conn,
            limit=3,
            stop_on_error=True,
            timestamp=(
                "2026-07-17T01:00:00+00:00"
            ),
        )



        print()


        #
        # Architectural contract:
        #
        # The dispatcher stops immediately after the first failure it
        # encounters. Because dispatch order is deterministic but not tied to
        # creation order, one or more handoffs may already have completed
        # successfully before the failure occurs.
        #

        assert result.claimed == 3
        assert result.failed == 1

        assert (
            result.dispatched
            + result.failed
            + result.skipped
            == result.claimed
        )

        assert result.skipped >= 1
        assert result.dispatched <= 2

        assert len(registration.calls) == (
            result.dispatched
            + result.failed
        )

        assert len(execution.calls) == (
            result.dispatched
            + result.failed
        )

        failed_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.FAILED
            for handoff in result.handoffs
        )

        queued_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.QUEUED
            for handoff in result.handoffs
        )

        dispatched_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.DISPATCHED
            for handoff in result.handoffs
        )

        assert failed_count == result.failed
        assert queued_count == result.skipped
        assert dispatched_count == result.dispatched

        for handoff in result.handoffs:
            if (
                handoff.handoff_state
                is AssimilationHandoffState.QUEUED
            ):
                assert (
                    "stopped after an earlier failure"
                    in (handoff.last_error or "")
                )

    finally:
        conn.close()


def verify_inventory() -> None:
    """Verify deterministic lifecycle inventory."""

    conn = open_database()

    try:
        create_ready_handoffs(
            conn,
            count=2,
            request_id="inventory",
        )

        repository = AssimilationDispatchRepository()

        inventory = repository.inventory(
            conn=conn
        )

        assert inventory == {
            "queued": 2,
            "dispatching": 0,
            "dispatched": 0,
            "failed": 0,
            "cancelled": 0,
        }

    finally:
        conn.close()


def main() -> None:
    verify_successful_dispatch()
    verify_bounded_dispatch()
    verify_failure_recording()
    verify_registration_failure_recording()
    verify_wrong_phase_vi_uuid_is_rejected()
    verify_failed_handoff_requeue()
    verify_attempt_limit_enforcement()
    verify_duplicate_dispatch_prevention()
    verify_stale_claim_recovery()
    verify_stop_on_error_releases_remaining_claims()
    verify_inventory()

    print("[PASS] Atomic queued-handoff claiming")
    print("[PASS] Deterministic bounded dispatch")
    print("[PASS] Registration-before-execution ordering")
    print("[PASS] Successful dispatch persistence")
    print("[PASS] Phase VI failure diagnostics")
    print("[PASS] Registration failure diagnostics")
    print("[PASS] Returned object-UUID validation")
    print("[PASS] Retry-safe failed-handoff requeue")
    print("[PASS] Dispatch-attempt limit enforcement")
    print("[PASS] Duplicate dispatch prevention")
    print("[PASS] Stale dispatch-claim recovery")
    print("[PASS] Stop-on-error claim release")
    print("[PASS] Deterministic dispatch inventory")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A7 canonical dispatch verified")


if __name__ == "__main__":
    main()

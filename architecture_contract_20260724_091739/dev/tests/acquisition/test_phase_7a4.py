"""
Phase VII-A4 durable admission workflow verification.

All persistence occurs in temporary in-memory SQLite databases.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import FrozenInstanceError

from knowledge_engine.acquisition.admission import (
    AdmissionAction,
)
from knowledge_engine.acquisition.intake import (
    AcquisitionIntakeResult,
    AcquisitionIntakeService,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


def make_candidate(
    *,
    filename: str,
    source_uri: str,
    content: bytes,
    extension: str = ".txt",
    candidate_type: str = "document",
) -> SourceCandidate:
    """Create one deterministic intake candidate."""

    return SourceCandidate(
        provider_id="filesystem",
        source_uri=source_uri,
        local_path=f"/tmp/{filename}",
        filename=filename,
        extension=extension,
        media_type="text/plain",
        candidate_type=candidate_type,
        size_bytes=len(content),
        checksum_sha256=hashlib.sha256(
            content
        ).hexdigest(),
    )


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    try:
        setattr(
            instance,
            attribute_name,
            replacement,
        )
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def verify_first_sighting(
    conn: sqlite3.Connection,
    service: AcquisitionIntakeService,
) -> AcquisitionIntakeResult:
    candidate = make_candidate(
        filename="alpha.txt",
        source_uri="file:///tmp/alpha.txt",
        content=b"alpha knowledge",
    )

    result = service.evaluate_and_record(
        conn=conn,
        candidate=candidate,
        campaign_id="phase-7a4",
        seen_at="2026-07-15T13:00:00+00:00",
    )

    assert result.action == "accept"
    assert result.decision.action is AdmissionAction.ACCEPT
    assert result.admitted is True
    assert result.already_known is False
    assert result.created is True
    assert result.sighting_count == 1
    assert result.known_checksum_count == 0

    assert (
        result.provenance.record.campaign_id
        == "phase-7a4"
    )

    assert_frozen(
        result,
        "known_checksum_count",
        999,
    )

    return result


def verify_repeat_sighting(
    conn: sqlite3.Connection,
    service: AcquisitionIntakeService,
    first: AcquisitionIntakeResult,
) -> None:
    candidate = make_candidate(
        filename="alpha.txt",
        source_uri="file:///tmp/alpha.txt",
        content=b"alpha knowledge",
    )

    repeat = service.evaluate_and_record(
        conn=conn,
        candidate=candidate,
        campaign_id="phase-7a4",
        seen_at="2026-07-15T14:00:00+00:00",
    )

    assert repeat.action == "ignore"
    assert repeat.decision.action is AdmissionAction.IGNORE
    assert repeat.admitted is False
    assert repeat.already_known is True
    assert repeat.created is False
    assert repeat.candidate_id == first.candidate_id
    assert repeat.sighting_count == 2
    assert repeat.known_checksum_count == 1

    history = (
        service.provenance_service.repository
        .list_history(
            conn=conn,
            candidate_id=repeat.candidate_id,
        )
    )

    assert len(history) == 2
    assert history[0].action == "accept"
    assert history[1].action == "ignore"


def verify_mirror_detection(
    conn: sqlite3.Connection,
    service: AcquisitionIntakeService,
) -> None:
    mirror = make_candidate(
        filename="alpha-mirror.txt",
        source_uri="file:///mirror/alpha.txt",
        content=b"alpha knowledge",
    )

    result = service.evaluate_and_record(
        conn=conn,
        candidate=mirror,
        campaign_id="mirror-campaign",
        seen_at="2026-07-15T15:00:00+00:00",
    )

    assert result.action == "ignore"
    assert result.already_known is True
    assert result.created is True
    assert result.sighting_count == 1
    assert result.known_checksum_count == 1

    matches = (
        service.provenance_service.repository
        .find_by_checksum(
            conn=conn,
            checksum_sha256=mirror.checksum_sha256,
        )
    )

    assert len(matches) == 2

    candidate_ids = {
        match.candidate_id
        for match in matches
    }

    assert len(candidate_ids) == 2


def verify_unique_second_document(
    conn: sqlite3.Connection,
    service: AcquisitionIntakeService,
) -> None:
    candidate = make_candidate(
        filename="bravo.txt",
        source_uri="file:///tmp/bravo.txt",
        content=b"bravo knowledge",
    )

    result = service.evaluate_and_record(
        conn=conn,
        candidate=candidate,
        seen_at="2026-07-15T16:00:00+00:00",
    )

    assert result.action == "accept"
    assert result.admitted is True
    assert result.already_known is False
    assert result.created is True

    # Alpha exists. Bravo's checksum is new.
    assert result.known_checksum_count == 1


def verify_rejected_candidate_is_remembered(
    conn: sqlite3.Connection,
    service: AcquisitionIntakeService,
) -> None:
    candidate = make_candidate(
        filename="danger.exe",
        source_uri="file:///tmp/danger.exe",
        content=b"MZ executable fixture",
        extension=".exe",
        candidate_type="generic_file",
    )

    result = service.evaluate_and_record(
        conn=conn,
        candidate=candidate,
        seen_at="2026-07-15T17:00:00+00:00",
    )

    assert result.action == "reject"
    assert result.admitted is False
    assert result.created is True
    assert result.provenance.record.last_action == "reject"

    history = (
        service.provenance_service.repository
        .list_history(
            conn=conn,
            candidate_id=result.candidate_id,
        )
    )

    assert len(history) == 1
    assert history[0].action == "reject"


def verify_transaction_rollback() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    service = AcquisitionIntakeService()

    candidate = make_candidate(
        filename="rollback.txt",
        source_uri="file:///tmp/rollback.txt",
        content=b"rollback fixture",
    )

    try:
        conn.execute("BEGIN")

        service.evaluate_and_record(
            conn=conn,
            candidate=candidate,
            seen_at="2026-07-15T18:00:00+00:00",
        )

        conn.rollback()

        record = (
            service.provenance_service.repository
            .get_by_source(
                conn=conn,
                provider_id=candidate.provider_id,
                source_uri=candidate.source_uri,
            )
        )

        assert record is None
    finally:
        conn.close()


def verify_input_validation() -> None:
    service = AcquisitionIntakeService()
    conn = sqlite3.connect(":memory:")

    try:
        try:
            service.evaluate_and_record(
                conn=conn,
                candidate="not-a-candidate",  # type: ignore[arg-type]
            )
        except TypeError as exc:
            assert "SourceCandidate" in str(exc)
        else:
            raise AssertionError(
                "Invalid candidate was accepted"
            )
    finally:
        conn.close()


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")

    service = AcquisitionIntakeService()

    try:
        conn.execute("BEGIN")

        first = verify_first_sighting(
            conn,
            service,
        )

        verify_repeat_sighting(
            conn,
            service,
            first,
        )

        verify_mirror_detection(
            conn,
            service,
        )

        verify_unique_second_document(
            conn,
            service,
        )

        verify_rejected_candidate_is_remembered(
            conn,
            service,
        )

        conn.commit()
    finally:
        conn.close()

    verify_transaction_rollback()
    verify_input_validation()

    print("[PASS] First-seen candidate admission")
    print("[PASS] Durable checksum lookup")
    print("[PASS] Repeat-sighting duplicate ignore")
    print("[PASS] Same-content mirror detection")
    print("[PASS] Unique-content admission")
    print("[PASS] Rejected-candidate provenance")
    print("[PASS] Complete admission history")
    print("[PASS] Caller-owned transaction rollback")
    print("[PASS] Intake input validation")
    print("[PASS] Immutable intake result")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A4 durable admission workflow verified")


if __name__ == "__main__":
    main()

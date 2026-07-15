"""
Phase VII-A3 provenance persistence verification.

All persistence occurs in a temporary in-memory SQLite database.
"""

from __future__ import annotations

import sqlite3
from dataclasses import FrozenInstanceError

from dev.tests.acquisition.fixtures import (
    make_candidate,
    make_context,
)
from knowledge_engine.acquisition.admission import (
    build_default_admission_director,
)
from knowledge_engine.acquisition.provenance import (
    ProvenanceService,
    build_candidate_id,
    ensure_provenance_schema,
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


def verify_schema_idempotency(
    conn: sqlite3.Connection,
) -> None:
    ensure_provenance_schema(conn)
    ensure_provenance_schema(conn)

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

    assert "acquisition_provenance" in tables
    assert "acquisition_admission_history" in tables


def verify_first_sighting(
    conn: sqlite3.Connection,
) -> str:
    candidate = make_candidate(
        filename="provenance.txt",
        content=b"persistent provenance",
    )

    decision = (
        build_default_admission_director()
        .evaluate_candidate(
            candidate=candidate,
            context=make_context(),
        )
    )

    service = ProvenanceService()

    result = service.record_decision(
        conn=conn,
        decision=decision,
        seen_at="2026-07-15T10:00:00+00:00",
        campaign_id="phase-7a3",
    )

    assert result.created is True
    assert result.sighting_count == 1
    assert result.record.first_seen_at == (
        "2026-07-15T10:00:00+00:00"
    )
    assert result.record.last_seen_at == (
        "2026-07-15T10:00:00+00:00"
    )
    assert result.record.last_action == "accept"
    assert result.record.campaign_id == "phase-7a3"
    assert result.history.action == "accept"

    expected_id = build_candidate_id(
        provider_id=candidate.provider_id,
        source_uri=candidate.source_uri,
    )

    assert result.candidate_id == expected_id

    assert_frozen(
        result.record,
        "sighting_count",
        99,
    )

    return result.candidate_id


def verify_repeat_sighting(
    conn: sqlite3.Connection,
    candidate_id: str,
) -> None:
    candidate = make_candidate(
        filename="provenance.txt",
        content=b"persistent provenance",
    )

    director = build_default_admission_director()

    first_context = make_context()

    first_decision = director.evaluate_candidate(
        candidate=candidate,
        context=first_context,
    )

    service = ProvenanceService()

    repeat = service.record_decision(
        conn=conn,
        decision=first_decision,
        seen_at="2026-07-15T11:00:00+00:00",
        campaign_id="phase-7a3",
    )

    assert repeat.created is False
    assert repeat.candidate_id == candidate_id
    assert repeat.sighting_count == 2
    assert repeat.record.first_seen_at == (
        "2026-07-15T10:00:00+00:00"
    )
    assert repeat.record.last_seen_at == (
        "2026-07-15T11:00:00+00:00"
    )

    history = service.repository.list_history(
        conn=conn,
        candidate_id=candidate_id,
    )

    assert len(history) == 2
    assert history[0].seen_at == (
        "2026-07-15T10:00:00+00:00"
    )
    assert history[1].seen_at == (
        "2026-07-15T11:00:00+00:00"
    )


def verify_checksum_lookup(
    conn: sqlite3.Connection,
) -> None:
    service = ProvenanceService()

    checksums = service.known_checksums(
        conn=conn
    )

    assert len(checksums) == 1

    checksum = next(iter(checksums))

    matches = service.repository.find_by_checksum(
        conn=conn,
        checksum_sha256=checksum,
    )

    assert len(matches) == 1
    assert matches[0].filename == "provenance.txt"


def verify_same_content_different_source(
    conn: sqlite3.Connection,
) -> None:
    first = make_candidate(
        filename="mirror-a.txt",
        content=b"mirrored content",
    )

    second = make_candidate(
        filename="mirror-b.txt",
        content=b"mirrored content",
    )

    director = build_default_admission_director()
    service = ProvenanceService()

    first_result = service.record_decision(
        conn=conn,
        decision=director.evaluate_candidate(
            candidate=first,
            context=make_context(),
        ),
        seen_at="2026-07-15T12:00:00+00:00",
    )

    second_result = service.record_decision(
        conn=conn,
        decision=director.evaluate_candidate(
            candidate=second,
            context=make_context(),
        ),
        seen_at="2026-07-15T12:01:00+00:00",
    )

    assert (
        first_result.candidate_id
        != second_result.candidate_id
    )

    matches = service.repository.find_by_checksum(
        conn=conn,
        checksum_sha256=first.checksum_sha256,
    )

    assert len(matches) == 2


def main() -> None:
    conn = sqlite3.connect(":memory:")

    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN")

        verify_schema_idempotency(conn)

        candidate_id = verify_first_sighting(conn)

        verify_repeat_sighting(
            conn,
            candidate_id,
        )

        verify_checksum_lookup(conn)
        verify_same_content_different_source(conn)

        conn.commit()
    finally:
        conn.close()

    print("[PASS] Provenance schema idempotency")
    print("[PASS] Deterministic source identity")
    print("[PASS] First-sighting persistence")
    print("[PASS] Repeat-sighting updates")
    print("[PASS] First-seen timestamp preservation")
    print("[PASS] Last-seen timestamp updates")
    print("[PASS] Admission history preservation")
    print("[PASS] Durable checksum inventory")
    print("[PASS] Same-content mirror detection")
    print("[PASS] Immutable provenance contracts")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A3 provenance persistence verified")


if __name__ == "__main__":
    main()

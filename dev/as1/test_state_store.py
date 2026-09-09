from __future__ import annotations

import sqlite3
import tempfile

from pathlib import Path

from dev.as1.state_store import (
    FINGERPRINT_VERSION,
    StoredFingerprint,
    complete_run,
    initialize_schema,
    open_state,
    start_run,
    upsert_fingerprint,
    upsert_object_state,
)


def main():

    with tempfile.TemporaryDirectory() as tmp:

        db = Path(tmp) / "state.sqlite"

        conn = open_state(db)

        initialize_schema(conn)

        run_id = start_run(
            conn,
            "unit_test",
        )

        fp = StoredFingerprint(
            file_path="/tmp/manual.pdf",
            source_kind="test",
            runtime_document_id=None,
            legacy_document_id=1,
            sha256="a" * 64,
            normalized_content_sha256="b" * 64,
            simhash64_hex="0123456789abcdef",
            normalized_chars=1000,
            normalized_title="manual",
            size_bytes=2000,
            mtime_ns=123,
            fingerprint_version=
                FINGERPRINT_VERSION,
        )

        assert upsert_fingerprint(
            conn,
            fp,
        ) is True

        # Idempotency.
        assert upsert_fingerprint(
            conn,
            fp,
        ) is False

        upsert_object_state(
            conn,
            file_path=fp.file_path,
            lifecycle=
                "BRIDGE_TO_CANONICAL_DISCOVERY",
            object_role="DOCUMENT",
            handler="document_text",
            identity_verdict="UNRESOLVED",
            identity_layer="bounded_sql",
            identity_confidence=0.50,
            matched_path=None,
            review_required=True,
            review_reason=
                "Persistent fingerprint index incomplete.",
            fingerprinted=True,
        )

        complete_run(
            conn,
            run_id,
            status="pass",
            objects_examined=1,
            objects_changed=1,
        )

        fp_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_identity_fingerprints
            """
        ).fetchone()[0]

        state_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_object_state
            """
        ).fetchone()[0]

        run_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM as1_runs
            """
        ).fetchone()[0]

        assert fp_count == 1
        assert state_count == 1
        assert run_count == 1

        conn.close()

    print(
        "GENESIS AS1 PACK 3 "
        "STATE STORE TESTS: PASS"
    )


if __name__ == "__main__":
    main()

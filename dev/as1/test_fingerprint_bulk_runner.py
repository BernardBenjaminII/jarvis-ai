from __future__ import annotations

import sqlite3
import tempfile

from pathlib import Path

from dev.as1.fingerprint_bulk_runner import (
    integrity_check,
    progress_percent,
    remaining_rows,
    snapshot,
)

from dev.as1.state_store import (
    FINGERPRINT_VERSION,
    StoredFingerprint,
    initialize_schema,
    open_state,
    simhash_to_hex,
    upsert_fingerprint,
)


def main():

    assert progress_percent(
        50,
        100,
    ) == 50.0

    assert progress_percent(
        0,
        0,
    ) == 100.0

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        runtime_db = (
            root / "runtime.sqlite"
        )

        state_db = (
            root / "state.sqlite"
        )

        runtime = sqlite3.connect(
            runtime_db
        )

        runtime.execute(
            """
            CREATE TABLE runtime_documents (
                id INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL,
                content_text TEXT NOT NULL,
                content_chars INTEGER NOT NULL
            )
            """
        )

        for i in range(1, 11):
            text = (
                f"Document {i} "
                * 10
            )

            runtime.execute(
                """
                INSERT INTO runtime_documents(
                    id,
                    file_path,
                    sha256,
                    title,
                    media_type,
                    content_text,
                    content_chars
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    f"/tmp/doc{i}.txt",
                    f"{i:064x}",
                    f"Document {i}",
                    "text/plain",
                    text,
                    len(text),
                ),
            )

        runtime.commit()
        runtime.close()

        state = open_state(
            state_db
        )

        initialize_schema(state)

        state.execute(
            """
            INSERT INTO as1_metadata(
                key,
                value
            )
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (
                "runtime_backfill_checkpoint_"
                + FINGERPRINT_VERSION,
                "2",
            ),
        )

        state.commit()

        for i in (1, 2):
            fp = StoredFingerprint(
                file_path=f"/tmp/doc{i}.txt",
                source_kind="runtime",
                runtime_document_id=i,
                legacy_document_id=None,
                sha256=f"{i:064x}",
                normalized_content_sha256=
                    f"{i + 100:064x}",
                simhash64_hex=
                    simhash_to_hex(i),
                normalized_chars=100,
                normalized_title=
                    f"document {i}",
                size_bytes=0,
                mtime_ns=None,
                fingerprint_version=
                    FINGERPRINT_VERSION,
            )

            upsert_fingerprint(
                state,
                fp,
            )

        state.close()

        snap = snapshot(
            runtime_db=runtime_db,
            state_db=state_db,
        )

        assert snap.checkpoint == 2
        assert snap.runtime_fingerprints == 2
        assert snap.runtime_rows == 10
        assert snap.runtime_max_id == 10

        assert remaining_rows(
            runtime_db,
            2,
        ) == 8

        ok, result = integrity_check(
            state_db
        )

        assert ok is True
        assert result == "ok"

    print(
        "GENESIS AS1 PACK 3A-R2 "
        "BULK RUNNER TESTS: PASS"
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from dev.as1.fingerprint_backfill import (
    RuntimeMetadata,
    get_content_text,
    get_metadata_batch,
)

from dev.as1.state_store import (
    initialize_schema,
    open_state,
)


def main():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        runtime_path = (
            root / "runtime.sqlite"
        )

        state_path = (
            root / "state.sqlite"
        )

        runtime = sqlite3.connect(
            runtime_path
        )

        runtime.row_factory = sqlite3.Row

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
                f"Document {i} content. "
                * 100
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

        batch = get_metadata_batch(
            runtime,
            after_id=0,
            batch_size=3,
        )

        assert len(batch) == 3
        assert batch[0].id == 1
        assert batch[-1].id == 3

        batch2 = get_metadata_batch(
            runtime,
            after_id=3,
            batch_size=3,
        )

        assert [
            item.id
            for item in batch2
        ] == [4, 5, 6]

        text = get_content_text(
            runtime,
            5,
        )

        assert text is not None
        assert "Document 5" in text

        state = open_state(
            state_path
        )

        initialize_schema(
            state
        )

        assert state.execute(
            """
            SELECT COUNT(*)
            FROM as1_metadata
            """
        ).fetchone()[0] > 0

        state.close()
        runtime.close()

    print(
        "GENESIS AS1 PACK 3A "
        "BACKFILL TESTS: PASS"
    )


if __name__ == "__main__":
    main()

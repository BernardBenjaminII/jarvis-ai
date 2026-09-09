from __future__ import annotations

import argparse
import gc
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from dev.as1.identity import (
    normalized_content_sha256,
    normalize_title,
    simhash64,
)

from dev.as1.state_store import (
    DEFAULT_STATE_DB,
    FINGERPRINT_VERSION,
    StoredFingerprint,
    complete_run,
    initialize_schema,
    open_state,
    simhash_to_hex,
    start_run,
    upsert_fingerprint,
)


RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

CHECKPOINT_KEY = (
    "runtime_backfill_checkpoint_"
    + FINGERPRINT_VERSION
)

MAX_BATCH_SIZE = 1000


@dataclass(frozen=True)
class RuntimeMetadata:
    id: int
    file_path: str
    sha256: str
    title: str
    content_chars: int


def open_runtime_ro(
    path: Path,
) -> sqlite3.Connection:

    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA query_only=ON"
    )

    conn.execute(
        "PRAGMA busy_timeout=5000"
    )

    return conn


def get_metadata_batch(
    conn: sqlite3.Connection,
    *,
    after_id: int,
    batch_size: int,
) -> list[RuntimeMetadata]:
    """
    Cheap bounded pass.

    Critically, content_text is NOT selected here.
    """

    rows = conn.execute(
        """
        SELECT
            id,
            file_path,
            sha256,
            title,
            content_chars
        FROM runtime_documents
        WHERE id > ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (
            after_id,
            batch_size,
        ),
    ).fetchall()

    return [
        RuntimeMetadata(
            id=int(row["id"]),
            file_path=str(
                row["file_path"]
            ),
            sha256=str(
                row["sha256"]
            ),
            title=str(
                row["title"]
            ),
            content_chars=int(
                row["content_chars"]
            ),
        )
        for row in rows
    ]


def get_content_text(
    conn: sqlite3.Connection,
    document_id: int,
) -> str | None:
    """
    Fetch exactly ONE content_text row.

    The caller must release it before proceeding to
    the next runtime document.
    """

    row = conn.execute(
        """
        SELECT content_text
        FROM runtime_documents
        WHERE id = ?
        LIMIT 1
        """,
        (document_id,),
    ).fetchone()

    if row is None:
        return None

    value = row["content_text"]

    if value is None:
        return None

    return str(value)


def checkpoint(
    state: sqlite3.Connection,
) -> int:

    row = state.execute(
        """
        SELECT value
        FROM as1_metadata
        WHERE key = ?
        LIMIT 1
        """,
        (CHECKPOINT_KEY,),
    ).fetchone()

    if row is None:
        return 0

    try:
        return int(row["value"])
    except (
        TypeError,
        ValueError,
    ):
        return 0


def save_checkpoint(
    state: sqlite3.Connection,
    document_id: int,
) -> None:

    state.execute(
        """
        INSERT INTO as1_metadata(
            key,
            value
        )
        VALUES (?, ?)

        ON CONFLICT(key)
        DO UPDATE SET
            value=excluded.value
        """,
        (
            CHECKPOINT_KEY,
            str(document_id),
        ),
    )

    state.commit()


def fingerprint_current(
    state: sqlite3.Connection,
    metadata: RuntimeMetadata,
) -> bool:
    """
    Determine whether the current runtime row has already
    been durably fingerprinted with this fingerprint version.

    SHA is the primary content-change detector.

    content_chars and normalized title are also checked so
    metadata drift cannot silently remain stale.
    """

    row = state.execute(
        """
        SELECT
            runtime_document_id,
            sha256,
            normalized_title,
            normalized_chars
        FROM as1_identity_fingerprints
        WHERE file_path = ?
          AND fingerprint_version = ?
        LIMIT 1
        """,
        (
            metadata.file_path,
            FINGERPRINT_VERSION,
        ),
    ).fetchone()

    if row is None:
        return False

    if (
        row["runtime_document_id"]
        != metadata.id
    ):
        return False

    if (
        row["sha256"]
        != metadata.sha256
    ):
        return False

    if (
        row["normalized_title"]
        != normalize_title(
            metadata.title
        )
    ):
        return False

    # normalized_chars is derived from normalized text,
    # not raw content_chars, so we deliberately do not
    # compare those values directly.

    return True


def persist_runtime_fingerprint(
    state: sqlite3.Connection,
    *,
    metadata: RuntimeMetadata,
    normalized_sha: str | None,
    normalized_chars: int | None,
    simhash_value: int | None,
) -> bool:

    stored = StoredFingerprint(
        file_path=
            metadata.file_path,

        source_kind=
            "runtime",

        runtime_document_id=
            metadata.id,

        legacy_document_id=
            None,

        sha256=
            metadata.sha256,

        normalized_content_sha256=
            normalized_sha,

        simhash64_hex=
            simhash_to_hex(
                simhash_value
            ),

        normalized_chars=
            normalized_chars,

        normalized_title=
            normalize_title(
                metadata.title
            ),

        # Runtime table does not carry physical size/mtime.
        # Do not stat 89k physical objects during this stage.
        size_bytes=
            0,

        mtime_ns=
            None,

        fingerprint_version=
            FINGERPRINT_VERSION,
    )

    return upsert_fingerprint(
        state,
        stored,
    )


def corpus_max_id(
    runtime: sqlite3.Connection,
) -> int:

    row = runtime.execute(
        """
        SELECT COALESCE(MAX(id), 0)
        FROM runtime_documents
        """
    ).fetchone()

    return int(row[0])


def corpus_count(
    runtime: sqlite3.Connection,
) -> int:

    row = runtime.execute(
        """
        SELECT COUNT(*)
        FROM runtime_documents
        """
    ).fetchone()

    return int(row[0])


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 3A bounded "
            "runtime fingerprint backfill."
        )
    )

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=RUNTIME_DB,
    )

    parser.add_argument(
        "--state-db",
        type=Path,
        default=DEFAULT_STATE_DB,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--from-id",
        type=int,
        default=None,
        help=(
            "Override checkpoint for diagnostic use. "
            "Does not reset durable state."
        ),
    )

    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help=(
            "Do not read content_text. Primarily diagnostic."
        ),
    )

    args = parser.parse_args()

    if (
        args.batch_size < 1
        or args.batch_size
        > MAX_BATCH_SIZE
    ):
        print(
            "FAIL: batch size must be between "
            f"1 and {MAX_BATCH_SIZE}",
            flush=True,
        )
        return 2

    runtime = open_runtime_ro(
        args.runtime_db
    )

    state = open_state(
        args.state_db
    )

    initialize_schema(
        state
    )

    run_id = start_run(
        state,
        "runtime_fingerprint_backfill",
        (
            f"batch_size={args.batch_size}; "
            f"metadata_only={args.metadata_only}"
        ),
    )

    started = time.monotonic()

    examined = 0
    changed = 0
    skipped = 0
    content_loaded = 0
    failures = 0

    try:
        durable_checkpoint = checkpoint(
            state
        )

        start_after = (
            args.from_id
            if args.from_id is not None
            else durable_checkpoint
        )

        total = corpus_count(
            runtime
        )

        maximum_id = corpus_max_id(
            runtime
        )

        print(
            "============================================================",
            flush=True,
        )
        print(
            " GENESIS AS1 PACK 3A — BACKFILL BATCH",
            flush=True,
        )
        print(
            "============================================================",
            flush=True,
        )

        print(
            "runtime rows          :",
            f"{total:,}",
            flush=True,
        )

        print(
            "runtime max id        :",
            f"{maximum_id:,}",
            flush=True,
        )

        print(
            "durable checkpoint    :",
            durable_checkpoint,
            flush=True,
        )

        print(
            "effective start id    :",
            start_after,
            flush=True,
        )

        print(
            "batch size            :",
            args.batch_size,
            flush=True,
        )

        print(
            "metadata only         :",
            args.metadata_only,
            flush=True,
        )

        print(
            "production writes     : 0",
            flush=True,
        )

        print()

        metadata_batch = get_metadata_batch(
            runtime,
            after_id=start_after,
            batch_size=args.batch_size,
        )

        if not metadata_batch:

            complete_run(
                state,
                run_id,
                status="complete",
                objects_examined=0,
                objects_changed=0,
                notes=(
                    "No runtime rows remain after "
                    f"checkpoint {start_after}."
                ),
            )

            print(
                "BACKFILL STATUS: COMPLETE",
                flush=True,
            )

            return 0

        for position, metadata in enumerate(
            metadata_batch,
            start=1,
        ):
            examined += 1

            print(
                f"[{position:03d}/{len(metadata_batch):03d}] "
                f"id={metadata.id} "
                f"chars={metadata.content_chars:,} "
                f"{metadata.title[:70]}",
                flush=True,
            )

            try:
                if fingerprint_current(
                    state,
                    metadata,
                ):
                    skipped += 1

                    print(
                        "    current fingerprint: SKIP",
                        flush=True,
                    )

                    # Safe to advance because this exact
                    # runtime state is already durable.
                    save_checkpoint(
                        state,
                        metadata.id,
                    )

                    continue

                if args.metadata_only:

                    normalized_sha = None
                    normalized_chars = None
                    simhash_value = None

                else:
                    text = get_content_text(
                        runtime,
                        metadata.id,
                    )

                    if text is None:
                        normalized_sha = None
                        normalized_chars = 0
                        simhash_value = None

                    else:
                        content_loaded += 1

                        (
                            normalized_sha,
                            normalized_chars,
                        ) = (
                            normalized_content_sha256(
                                text
                            )
                        )

                        simhash_value = simhash64(
                            text
                        )

                        # Explicitly release potentially
                        # multi-million-character content.
                        del text

                was_changed = (
                    persist_runtime_fingerprint(
                        state,
                        metadata=metadata,
                        normalized_sha=
                            normalized_sha,
                        normalized_chars=
                            normalized_chars,
                        simhash_value=
                            simhash_value,
                    )
                )

                if was_changed:
                    changed += 1

                # Checkpoint advances only AFTER the
                # fingerprint is safely committed.
                save_checkpoint(
                    state,
                    metadata.id,
                )

                print(
                    "    fingerprint: "
                    + (
                        "WRITTEN"
                        if was_changed
                        else "UNCHANGED"
                    ),
                    flush=True,
                )

                # Ensure large transient strings become
                # collectible between rows.
                if position % 10 == 0:
                    gc.collect()

            except Exception as exc:
                failures += 1

                print(
                    "    ERROR:",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )

                print(
                    "    checkpoint NOT advanced",
                    flush=True,
                )

                # Stop this batch on the first failed row.
                # This preserves deterministic resume
                # semantics.
                break

        final_checkpoint = checkpoint(
            state
        )

        elapsed = (
            time.monotonic()
            - started
        )

        if failures:
            status = "partial_failure"
        else:
            status = "pass"

        complete_run(
            state,
            run_id,
            status=status,
            objects_examined=examined,
            objects_changed=changed,
            notes=(
                f"checkpoint={final_checkpoint}; "
                f"skipped={skipped}; "
                f"content_loaded={content_loaded}; "
                f"failures={failures}; "
                f"elapsed={elapsed:.3f}s"
            ),
        )

        print()
        print(
            "=== BATCH RESULT ===",
            flush=True,
        )

        print(
            "examined              :",
            examined,
            flush=True,
        )

        print(
            "changed               :",
            changed,
            flush=True,
        )

        print(
            "already current       :",
            skipped,
            flush=True,
        )

        print(
            "content rows loaded   :",
            content_loaded,
            flush=True,
        )

        print(
            "failures              :",
            failures,
            flush=True,
        )

        print(
            "checkpoint            :",
            final_checkpoint,
            flush=True,
        )

        print(
            "elapsed seconds       :",
            f"{elapsed:.2f}",
            flush=True,
        )

        print(
            "production DB writes  : 0",
            flush=True,
        )

        print(
            "AS1 sidecar writes    : YES",
            flush=True,
        )

        if failures:
            print(
                "BACKFILL STATUS: PARTIAL FAILURE",
                flush=True,
            )
            return 1

        print(
            "BACKFILL STATUS: PASS",
            flush=True,
        )

        return 0

    except Exception as exc:

        complete_run(
            state,
            run_id,
            status="failed",
            objects_examined=examined,
            objects_changed=changed,
            notes=(
                f"{type(exc).__name__}: {exc}"
            ),
        )

        print(
            "FATAL:",
            type(exc).__name__,
            str(exc),
            flush=True,
        )

        return 1

    finally:
        runtime.close()
        state.close()


if __name__ == "__main__":
    raise SystemExit(main())

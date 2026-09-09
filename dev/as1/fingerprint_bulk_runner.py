from __future__ import annotations

import argparse
import signal
import sqlite3
import subprocess
import sys
import time

from dataclasses import dataclass
from pathlib import Path

from dev.as1.state_store import (
    DEFAULT_STATE_DB,
    FINGERPRINT_VERSION,
)


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

CHECKPOINT_KEY = (
    "runtime_backfill_checkpoint_"
    + FINGERPRINT_VERSION
)

DEFAULT_BATCH_SIZE = 250
DEFAULT_MAX_DOCUMENTS = 2500

MAX_BATCH_SIZE = 1000
MAX_DOCUMENT_BUDGET = 100_000


@dataclass(frozen=True)
class Snapshot:
    checkpoint: int
    runtime_fingerprints: int
    runtime_rows: int
    runtime_max_id: int


STOP_REQUESTED = False


def request_stop(
    signum,
    frame,
):
    global STOP_REQUESTED
    STOP_REQUESTED = True

    print()
    print(
        "STOP REQUESTED — current worker will "
        "finish/return before runner exits.",
        flush=True,
    )


def open_ro(
    path: Path,
) -> sqlite3.Connection:

    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


def open_state_ro(
    path: Path,
) -> sqlite3.Connection:

    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


def checkpoint(
    state: sqlite3.Connection,
) -> int:

    row = state.execute(
        """
        SELECT value
        FROM as1_metadata
        WHERE key=?
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


def runtime_fingerprint_count(
    state: sqlite3.Connection,
) -> int:

    row = state.execute(
        """
        SELECT COUNT(*)
        FROM as1_identity_fingerprints
        WHERE source_kind='runtime'
          AND fingerprint_version=?
        """,
        (FINGERPRINT_VERSION,),
    ).fetchone()

    return int(row[0])


def runtime_stats(
    runtime: sqlite3.Connection,
) -> tuple[int, int]:

    row = runtime.execute(
        """
        SELECT
            COUNT(*) AS n,
            COALESCE(MAX(id), 0) AS max_id
        FROM runtime_documents
        """
    ).fetchone()

    return (
        int(row["n"]),
        int(row["max_id"]),
    )


def snapshot(
    *,
    runtime_db: Path,
    state_db: Path,
) -> Snapshot:

    runtime = open_ro(runtime_db)
    state = open_state_ro(state_db)

    try:
        rows, max_id = runtime_stats(
            runtime
        )

        return Snapshot(
            checkpoint=checkpoint(state),
            runtime_fingerprints=
                runtime_fingerprint_count(
                    state
                ),
            runtime_rows=rows,
            runtime_max_id=max_id,
        )

    finally:
        runtime.close()
        state.close()


def integrity_check(
    state_db: Path,
) -> tuple[bool, str]:

    state = open_state_ro(
        state_db
    )

    try:
        row = state.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        result = (
            str(row[0])
            if row is not None
            else "no result"
        )

        return (
            result.casefold() == "ok",
            result,
        )

    finally:
        state.close()


def remaining_rows(
    runtime_db: Path,
    after_id: int,
) -> int:

    runtime = open_ro(
        runtime_db
    )

    try:
        row = runtime.execute(
            """
            SELECT COUNT(*)
            FROM runtime_documents
            WHERE id > ?
            """,
            (after_id,),
        ).fetchone()

        return int(row[0])

    finally:
        runtime.close()


def run_worker(
    *,
    batch_size: int,
    runtime_db: Path,
    state_db: Path,
) -> int:
    """
    Execute the already-certified Pack 3A worker in a separate
    Python process.

    stdout/stderr are inherited so progress remains visible.
    """

    command = [
        sys.executable,
        "-m",
        "dev.as1.fingerprint_backfill",
        "--runtime-db",
        str(runtime_db),
        "--state-db",
        str(state_db),
        "--batch-size",
        str(batch_size),
    ]

    print()
    print(
        "WORKER COMMAND:",
        " ".join(command),
        flush=True,
    )

    completed = subprocess.run(
        command,
        check=False,
    )

    return int(
        completed.returncode
    )


def progress_percent(
    completed: int,
    total: int,
) -> float:

    if total <= 0:
        return 100.0

    return min(
        100.0,
        (
            completed
            / total
        )
        * 100.0,
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 3A-R2 controlled "
            "bulk fingerprint backfill runner."
        )
    )

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--state-db",
        type=Path,
        default=DEFAULT_STATE_DB,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
    )

    parser.add_argument(
        "--max-documents",
        type=int,
        default=DEFAULT_MAX_DOCUMENTS,
        help=(
            "Hard maximum number of runtime rows this "
            "invocation may advance across."
        ),
    )

    parser.add_argument(
        "--run-to-completion",
        action="store_true",
        help=(
            "Ignore --max-documents and continue until the "
            "runtime corpus is exhausted. Do not use until "
            "bounded production certification is complete."
        ),
    )

    parser.add_argument(
        "--integrity-every",
        type=int,
        default=2,
        help=(
            "Run sidecar integrity_check every N completed "
            "internal batches."
        ),
    )

    args = parser.parse_args()

    if (
        args.batch_size < 1
        or args.batch_size > MAX_BATCH_SIZE
    ):
        print(
            "FAIL: --batch-size must be between "
            f"1 and {MAX_BATCH_SIZE}",
            flush=True,
        )
        return 2

    if not args.run_to_completion:
        if (
            args.max_documents < 1
            or args.max_documents
            > MAX_DOCUMENT_BUDGET
        ):
            print(
                "FAIL: --max-documents must be between "
                f"1 and {MAX_DOCUMENT_BUDGET}",
                flush=True,
            )
            return 2

    if args.integrity_every < 1:
        print(
            "FAIL: --integrity-every must be >= 1",
            flush=True,
        )
        return 2

    if not args.runtime_db.is_file():
        print(
            "FAIL: runtime DB missing:",
            args.runtime_db,
            flush=True,
        )
        return 2

    if not args.state_db.is_file():
        print(
            "FAIL: AS1 sidecar missing:",
            args.state_db,
            flush=True,
        )
        return 2

    signal.signal(
        signal.SIGINT,
        request_stop,
    )

    signal.signal(
        signal.SIGTERM,
        request_stop,
    )

    initial = snapshot(
        runtime_db=args.runtime_db,
        state_db=args.state_db,
    )

    started = time.monotonic()

    budget_remaining = (
        None
        if args.run_to_completion
        else args.max_documents
    )

    batches_completed = 0
    worker_failures = 0
    stalled_batches = 0

    current = initial

    print(
        "============================================================",
        flush=True,
    )
    print(
        " GENESIS AS1 PACK 3A-R2 — BULK RUN",
        flush=True,
    )
    print(
        "============================================================",
        flush=True,
    )

    print(
        "runtime rows            :",
        f"{current.runtime_rows:,}",
        flush=True,
    )

    print(
        "runtime max id          :",
        f"{current.runtime_max_id:,}",
        flush=True,
    )

    print(
        "starting checkpoint     :",
        f"{current.checkpoint:,}",
        flush=True,
    )

    print(
        "starting fingerprints   :",
        f"{current.runtime_fingerprints:,}",
        flush=True,
    )

    print(
        "internal batch size     :",
        args.batch_size,
        flush=True,
    )

    print(
        "document budget         :",
        (
            "RUN TO COMPLETION"
            if args.run_to_completion
            else f"{args.max_documents:,}"
        ),
        flush=True,
    )

    print(
        "production DB writes    : 0",
        flush=True,
    )

    print()

    while True:

        if STOP_REQUESTED:
            print(
                "Runner stop acknowledged.",
                flush=True,
            )
            break

        remaining = remaining_rows(
            args.runtime_db,
            current.checkpoint,
        )

        if remaining <= 0:
            print(
                "Runtime corpus backfill is complete.",
                flush=True,
            )
            break

        if (
            budget_remaining is not None
            and budget_remaining <= 0
        ):
            print(
                "Invocation document budget reached.",
                flush=True,
            )
            break

        this_batch = min(
            args.batch_size,
            remaining,
        )

        if budget_remaining is not None:
            this_batch = min(
                this_batch,
                budget_remaining,
            )

        before = current

        batch_number = (
            batches_completed + 1
        )

        print()
        print(
            "------------------------------------------------------------",
            flush=True,
        )

        print(
            f" INTERNAL BATCH {batch_number}",
            flush=True,
        )

        print(
            " checkpoint before      :",
            before.checkpoint,
            flush=True,
        )

        print(
            " fingerprints before    :",
            before.runtime_fingerprints,
            flush=True,
        )

        print(
            " requested rows         :",
            this_batch,
            flush=True,
        )

        batch_started = (
            time.monotonic()
        )

        worker_rc = run_worker(
            batch_size=this_batch,
            runtime_db=args.runtime_db,
            state_db=args.state_db,
        )

        batch_elapsed = (
            time.monotonic()
            - batch_started
        )

        after = snapshot(
            runtime_db=args.runtime_db,
            state_db=args.state_db,
        )

        checkpoint_delta = (
            after.checkpoint
            - before.checkpoint
        )

        fingerprint_delta = (
            after.runtime_fingerprints
            - before.runtime_fingerprints
        )

        # Number of source rows advanced is better measured
        # from fingerprint delta for this contiguous backfill
        # phase. Existing-current rows can legitimately make
        # this lower, so checkpoint movement is authoritative.
        progressed = (
            after.checkpoint
            > before.checkpoint
        )

        print()
        print(
            "batch worker RC         :",
            worker_rc,
            flush=True,
        )

        print(
            "checkpoint after       :",
            after.checkpoint,
            flush=True,
        )

        print(
            "checkpoint delta       :",
            checkpoint_delta,
            flush=True,
        )

        print(
            "fingerprints after     :",
            after.runtime_fingerprints,
            flush=True,
        )

        print(
            "fingerprint delta      :",
            fingerprint_delta,
            flush=True,
        )

        print(
            "batch elapsed seconds  :",
            f"{batch_elapsed:.2f}",
            flush=True,
        )

        if worker_rc != 0:
            worker_failures += 1

            print(
                "STOP: worker returned failure.",
                flush=True,
            )

            current = after
            break

        if not progressed:
            stalled_batches += 1

            print(
                "STOP: checkpoint did not advance.",
                flush=True,
            )

            current = after
            break

        batches_completed += 1
        current = after

        if budget_remaining is not None:
            # Worker was asked for at most this_batch rows.
            # Deduct the requested successful batch ceiling.
            # At the corpus tail this_batch already reflects
            # actual remaining row count.
            budget_remaining -= this_batch

        coverage = progress_percent(
            current.runtime_fingerprints,
            current.runtime_rows,
        )

        total_elapsed = (
            time.monotonic()
            - started
        )

        print(
            "coverage                :",
            (
                f"{current.runtime_fingerprints:,}"
                f"/{current.runtime_rows:,} "
                f"({coverage:.3f}%)"
            ),
            flush=True,
        )

        print(
            "total elapsed seconds  :",
            f"{total_elapsed:.2f}",
            flush=True,
        )

        if (
            batches_completed
            % args.integrity_every
            == 0
        ):
            print()
            print(
                "AS1 SIDECAR INTEGRITY CHECK",
                flush=True,
            )

            ok, result = integrity_check(
                args.state_db
            )

            print(
                "integrity:",
                result,
                flush=True,
            )

            if not ok:
                print(
                    "STOP: sidecar integrity check failed.",
                    flush=True,
                )
                break

    final = snapshot(
        runtime_db=args.runtime_db,
        state_db=args.state_db,
    )

    elapsed = (
        time.monotonic()
        - started
    )

    final_integrity_ok, final_integrity = (
        integrity_check(
            args.state_db
        )
    )

    total_fingerprint_delta = (
        final.runtime_fingerprints
        - initial.runtime_fingerprints
    )

    final_coverage = progress_percent(
        final.runtime_fingerprints,
        final.runtime_rows,
    )

    if worker_failures:
        status = "FAILED_WORKER"

    elif stalled_batches:
        status = "STALLED"

    elif not final_integrity_ok:
        status = "FAILED_INTEGRITY"

    elif remaining_rows(
        args.runtime_db,
        final.checkpoint,
    ) == 0:
        status = "COMPLETE"

    elif STOP_REQUESTED:
        status = "INTERRUPTED_SAFE"

    else:
        status = "BUDGET_COMPLETE"

    print()
    print(
        "============================================================",
        flush=True,
    )

    print(
        " BULK RUN RESULT",
        flush=True,
    )

    print(
        "============================================================",
        flush=True,
    )

    print(
        "status                  :",
        status,
        flush=True,
    )

    print(
        "batches completed       :",
        batches_completed,
        flush=True,
    )

    print(
        "starting checkpoint     :",
        initial.checkpoint,
        flush=True,
    )

    print(
        "final checkpoint        :",
        final.checkpoint,
        flush=True,
    )

    print(
        "starting fingerprints   :",
        initial.runtime_fingerprints,
        flush=True,
    )

    print(
        "final fingerprints      :",
        final.runtime_fingerprints,
        flush=True,
    )

    print(
        "fingerprint delta       :",
        total_fingerprint_delta,
        flush=True,
    )

    print(
        "coverage                :",
        (
            f"{final.runtime_fingerprints:,}"
            f"/{final.runtime_rows:,} "
            f"({final_coverage:.3f}%)"
        ),
        flush=True,
    )

    print(
        "worker failures         :",
        worker_failures,
        flush=True,
    )

    print(
        "stalled batches         :",
        stalled_batches,
        flush=True,
    )

    print(
        "sidecar integrity       :",
        final_integrity,
        flush=True,
    )

    print(
        "elapsed seconds         :",
        f"{elapsed:.2f}",
        flush=True,
    )

    print(
        "production DB writes    : 0",
        flush=True,
    )

    print(
        "AS1 sidecar writes      : YES",
        flush=True,
    )

    if status in {
        "BUDGET_COMPLETE",
        "COMPLETE",
        "INTERRUPTED_SAFE",
    }:
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

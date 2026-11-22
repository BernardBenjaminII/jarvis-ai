"""R10.0A: durable, offline catalog-event ingestion.

Catalog: read-only.
Ledger: transactionally written.
Notifications and target execution: disabled.
"""

from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import stat
import time

from .changes_r922e2 import (
    SnapshotError,
    compare_records,
    validated_snapshot,
)


SCHEMA = "jarvis.bounty.operations.r10a"


class OperationsError(ValueError):
    pass


def default_catalog():
    root = Path(os.environ.get(
        "JARVIS_RUNTIME_ROOT",
        str(Path.home() / ".local/share/jarvis"),
    )).expanduser()
    return root / "bounty_catalog/r4.sqlite"


def default_ledger():
    root = Path(os.environ.get(
        "JARVIS_RUNTIME_ROOT",
        str(Path.home() / ".local/share/jarvis"),
    )).expanduser()
    return root / "bounty_operations/r10_events.sqlite3"


def response(status, **extra):
    return {
        "schema": SCHEMA,
        "status": status,
        "mode": "offline_catalog_ingestion",
        "network_requests": 0,
        "testing_authorized": False,
        "execution_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
        "new_events": 0,
        "processed_complete_runs": 0,
        **extra,
    }


def open_ledger(path):
    path.parent.mkdir(
        parents=True, exist_ok=True, mode=0o700
    )

    directory = path.parent.lstat()
    if (
        not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != os.getuid()
        or stat.S_IMODE(directory.st_mode) != 0o700
    ):
        raise OperationsError("Unsafe ledger directory")

    fd = os.open(
        path,
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o600,
    )

    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
        ):
            raise OperationsError("Unsafe ledger file")
    finally:
        os.close(fd)

    db = sqlite3.connect(
        path, timeout=10, isolation_level=None
    )
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")

        db.executescript("""
            CREATE TABLE IF NOT EXISTS applied_runs (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                previous_run_id TEXT,
                kind TEXT NOT NULL
                    CHECK(kind IN ('baseline','compared')),
                program_count INTEGER NOT NULL,
                applied_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS opportunity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL
                    REFERENCES applied_runs(run_id),
                handle TEXT NOT NULL,
                event_type TEXT NOT NULL,
                program TEXT NOT NULL,
                changed_fields_json TEXT NOT NULL,
                review_state TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                UNIQUE(run_id,handle)
            );
        """)
        return db
    except BaseException:
        db.close()
        raise


def ingest(catalog_path=None, ledger_path=None):
    catalog_path = Path(
        catalog_path or default_catalog()
    ).expanduser()
    ledger_path = Path(
        ledger_path or default_ledger()
    ).expanduser()

    if catalog_path.is_symlink():
        raise OperationsError("Catalog symlink forbidden")

    if not catalog_path.exists():
        return response("catalog_missing")

    if not catalog_path.is_file():
        raise OperationsError("Invalid catalog path")

    uri = catalog_path.resolve(
        strict=True
    ).as_uri() + "?mode=ro"

    try:
        with closing(sqlite3.connect(
            uri, uri=True, timeout=10
        )) as catalog:
            catalog.row_factory = sqlite3.Row
            catalog.execute("PRAGMA query_only=ON")

            runs = catalog.execute("""
                SELECT id, status, finished
                FROM runs
                WHERE source='hackerone-api'
                ORDER BY finished ASC, rowid ASC
            """).fetchall()

            if not runs:
                return response("catalog_empty")

            if runs[-1]["status"] != "complete":
                return response(
                    "blocked_latest_run_incomplete",
                    latest_run_status=runs[-1]["status"],
                )

            complete = [
                row for row in runs
                if row["status"] == "complete"
            ]

            if not complete:
                return response("no_complete_snapshot")

            with closing(open_ledger(ledger_path)) as db:
                db.execute("BEGIN IMMEDIATE")

                try:
                    last = db.execute("""
                        SELECT run_id
                        FROM applied_runs
                        ORDER BY sequence DESC
                        LIMIT 1
                    """).fetchone()

                    if last is None:
                        baseline = complete[-1]
                        snapshot = validated_snapshot(
                            catalog, baseline["id"]
                        )

                        db.execute("""
                            INSERT INTO applied_runs
                            (run_id, previous_run_id, kind,
                             program_count, applied_at)
                            VALUES (?,NULL,'baseline',?,?)
                        """, (
                            baseline["id"],
                            len(snapshot),
                            time.time(),
                        ))

                        result = response(
                            "baseline_established",
                            baseline_run_id=baseline["id"],
                            current_program_count=len(snapshot),
                            processed_complete_runs=1,
                        )

                    else:
                        ids = [
                            run["id"] for run in complete
                        ]

                        if last["run_id"] not in ids:
                            raise OperationsError(
                                "Last processed run missing "
                                "from complete catalog history"
                            )

                        position = ids.index(last["run_id"])
                        previous_id = ids[position]
                        previous = validated_snapshot(
                            catalog, previous_id
                        )

                        new_events = 0
                        processed = 0

                        for current_id in ids[position + 1:]:
                            current = validated_snapshot(
                                catalog, current_id
                            )

                            changes = compare_records(
                                previous, current
                            )

                            db.execute("""
                                INSERT INTO applied_runs
                                (run_id, previous_run_id, kind,
                                 program_count, applied_at)
                                VALUES (?,?,'compared',?,?)
                            """, (
                                current_id,
                                previous_id,
                                len(current),
                                time.time(),
                            ))

                            for event in changes:
                                db.execute("""
                                    INSERT INTO opportunity_events
                                    (run_id, handle, event_type,
                                     program, changed_fields_json,
                                     created_at)
                                    VALUES (?,?,?,?,?,?)
                                """, (
                                    current_id,
                                    event["handle"],
                                    event["type"],
                                    event["program"],
                                    json.dumps(
                                        event["changed_fields"],
                                        sort_keys=True,
                                    ),
                                    time.time(),
                                ))

                            new_events += len(changes)
                            processed += 1
                            previous_id = current_id
                            previous = current

                        result = response(
                            "ingested" if processed
                            else "up_to_date",
                            latest_processed_run_id=previous_id,
                            processed_complete_runs=processed,
                            new_events=new_events,
                        )

                    result["total_events"] = db.execute(
                        "SELECT COUNT(*) "
                        "FROM opportunity_events"
                    ).fetchone()[0]

                    result["pending_review"] = db.execute(
                        "SELECT COUNT(*) "
                        "FROM opportunity_events "
                        "WHERE review_state='pending'"
                    ).fetchone()[0]

                    db.commit()
                    return result

                except BaseException:
                    db.rollback()
                    raise

    except (sqlite3.Error, SnapshotError) as exc:
        raise OperationsError(
            "Catalog or operations ledger validation failed"
        ) from exc


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="R10 durable opportunity event ingestion"
    )
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()

    try:
        output = ingest(args.catalog, args.ledger)
    except OperationsError as exc:
        parser.error(str(exc))

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

"""R10.0B: persistent human-review queue and audit trail.

No network, target execution, mission creation, or notifications.
"""

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from .operations_r100a import default_ledger


SCHEMA = "jarvis.bounty.review_queue.r10b"

STATES = (
    "pending",
    "acknowledged",
    "deferred",
    "resolved",
)

TRANSITIONS = {
    "pending": {"acknowledged", "deferred", "resolved"},
    "acknowledged": {"deferred", "resolved"},
    "deferred": {"acknowledged", "resolved"},
    "resolved": {"pending"},
}


class ReviewError(ValueError):
    pass


def _path(path):
    path = Path(path or default_ledger()).expanduser()

    if path.is_symlink():
        raise ReviewError("Ledger symlink forbidden")

    if not path.exists():
        return None

    file_info = path.lstat()
    parent_info = path.parent.lstat()

    if (
        not stat.S_ISREG(file_info.st_mode)
        or file_info.st_uid != os.getuid()
        or stat.S_IMODE(file_info.st_mode) != 0o600
        or file_info.st_nlink != 1
    ):
        raise ReviewError("Unsafe ledger file")

    if (
        not stat.S_ISDIR(parent_info.st_mode)
        or parent_info.st_uid != os.getuid()
        or stat.S_IMODE(parent_info.st_mode) != 0o700
    ):
        raise ReviewError("Unsafe ledger directory")

    return path


def _connect(path, *, writable=False):
    uri = path.resolve(strict=True).as_uri()
    uri += "?mode=rw" if writable else "?mode=ro"

    db = sqlite3.connect(
        uri,
        uri=True,
        timeout=10,
        isolation_level=None,
    )
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA foreign_keys=ON")

    if not writable:
        db.execute("PRAGMA query_only=ON")

    return db


def _safety():
    return {
        "schema": SCHEMA,
        "network_requests": 0,
        "human_review_only": True,
        "testing_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
    }


def list_reviews(
    ledger_path=None,
    *,
    state=None,
    limit=50,
    offset=0,
):
    if state is not None and state not in STATES:
        raise ReviewError("Invalid review-state filter")

    if type(limit) is not int or not 1 <= limit <= 200:
        raise ReviewError("Invalid review limit")

    if type(offset) is not int or offset < 0:
        raise ReviewError("Invalid review offset")

    path = _path(ledger_path)

    if path is None:
        return {
            **_safety(),
            "status": "ledger_missing",
            "total_events": 0,
            "counts": {state: 0 for state in STATES},
            "records": [],
        }

    try:
        with closing(_connect(path)) as db:
            counts = {state: 0 for state in STATES}

            for row in db.execute(
                "SELECT review_state, COUNT(*) AS total "
                "FROM opportunity_events GROUP BY review_state"
            ):
                if row["review_state"] not in counts:
                    raise ReviewError("Unknown stored review state")
                counts[row["review_state"]] = row["total"]

            query = """
                SELECT e.id, e.run_id, a.previous_run_id,
                       e.handle, e.event_type, e.program,
                       e.changed_fields_json, e.review_state,
                       e.created_at
                FROM opportunity_events e
                JOIN applied_runs a ON a.run_id=e.run_id
            """
            parameters = []

            if state is not None:
                query += " WHERE e.review_state=?"
                parameters.append(state)

            query += (
                " ORDER BY e.created_at DESC, e.id DESC "
                "LIMIT ? OFFSET ?"
            )
            parameters.extend((limit, offset))

            records = []

            for row in db.execute(query, parameters):
                item = dict(row)
                item["changed_fields"] = json.loads(
                    item.pop("changed_fields_json")
                )
                item["human_review_required"] = True
                item["testing_authorized"] = False
                records.append(item)

            return {
                **_safety(),
                "status": "ready",
                "total_events": sum(counts.values()),
                "counts": counts,
                "limit": limit,
                "offset": offset,
                "records": records,
            }

    except (sqlite3.Error, ValueError, TypeError) as exc:
        raise ReviewError("Review queue unavailable") from exc



def get_review_history(
    event_id,
    ledger_path=None,
    *,
    limit=100,
    offset=0,
):
    """Read an opportunity's review audit trail without writes."""

    if type(event_id) is not int or event_id < 1:
        raise ReviewError("Invalid event ID")

    if type(limit) is not int or not 1 <= limit <= 200:
        raise ReviewError("Invalid history limit")

    if type(offset) is not int or offset < 0:
        raise ReviewError("Invalid history offset")

    path = _path(ledger_path)

    if path is None:
        raise ReviewError("Operations ledger does not exist")

    try:
        with closing(_connect(path)) as db:
            event = db.execute(
                "SELECT id, review_state "
                "FROM opportunity_events WHERE id=?",
                (event_id,),
            ).fetchone()

            if event is None:
                raise ReviewError("Unknown opportunity event")

            exists = db.execute("""
                SELECT 1 FROM sqlite_master
                WHERE type='table' AND name='review_history'
            """).fetchone()

            records = []
            total = 0

            if exists:
                total = db.execute(
                    "SELECT COUNT(*) FROM review_history "
                    "WHERE event_id=?",
                    (event_id,),
                ).fetchone()[0]

                rows = db.execute("""
                    SELECT id, request_id, from_state,
                           to_state, actor, note, changed_at
                    FROM review_history
                    WHERE event_id=?
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                """, (event_id, limit, offset))

                records = [dict(row) for row in rows]

            return {
                **_safety(),
                "status": "ready",
                "event_id": event_id,
                "review_state": event["review_state"],
                "total_history": total,
                "limit": limit,
                "offset": offset,
                "records": records,
            }

    except sqlite3.Error as exc:
        raise ReviewError(
            "Review history unavailable"
        ) from exc

def _operator_text(value, name, maximum):
    if (
        not isinstance(value, str)
        or not 1 <= len(value.strip()) <= maximum
        or any(ord(char) < 32 or ord(char) == 127
               for char in value)
    ):
        raise ReviewError("Invalid " + name)

    return value.strip()


def transition_review(
    event_id,
    *,
    expected_state,
    new_state,
    actor,
    request_id,
    note="",
    ledger_path=None,
):
    """Apply one explicit human review decision exactly once."""

    if type(event_id) is not int or event_id < 1:
        raise ReviewError("Invalid event ID")

    if expected_state not in STATES or new_state not in STATES:
        raise ReviewError("Invalid review state")

    actor = _operator_text(actor, "operator", 100)

    if (
        not isinstance(request_id, str)
        or re.fullmatch(
            r"[A-Za-z0-9._:-]{8,128}",
            request_id,
        ) is None
    ):
        raise ReviewError("Invalid idempotency key")

    if not isinstance(note, str) or len(note) > 400:
        raise ReviewError("Invalid review note")

    if any(ord(c) < 32 or ord(c) == 127 for c in note):
        raise ReviewError("Invalid review note")

    note = note.strip()
    path = _path(ledger_path)

    if path is None:
        raise ReviewError("Operations ledger does not exist")

    try:
        with closing(_connect(path, writable=True)) as db:
            db.execute("BEGIN IMMEDIATE")

            try:
                history_exists = db.execute("""
                    SELECT 1 FROM sqlite_master
                    WHERE type='table'
                      AND name='review_history'
                """).fetchone()

                if history_exists:
                    previous = db.execute("""
                        SELECT *
                        FROM review_history
                        WHERE request_id=?
                    """, (request_id,)).fetchone()

                    if previous is not None:
                        same_request = (
                            previous["event_id"] == event_id
                            and previous["from_state"] == expected_state
                            and previous["to_state"] == new_state
                            and previous["actor"] == actor
                            and previous["note"] == note
                        )

                        if not same_request:
                            raise ReviewError(
                                "Conflicting idempotency key"
                            )

                        db.commit()

                        return {
                            **_safety(),
                            "status": "already_applied",
                            "event_id": event_id,
                            "review_state": new_state,
                            "request_id": request_id,
                        }

                event = db.execute("""
                    SELECT review_state
                    FROM opportunity_events
                    WHERE id=?
                """, (event_id,)).fetchone()

                if event is None:
                    raise ReviewError("Unknown opportunity event")

                current_state = event["review_state"]

                if current_state != expected_state:
                    raise ReviewError(
                        "Review state changed; reload the queue"
                    )

                if new_state not in TRANSITIONS[current_state]:
                    raise ReviewError(
                        "Review transition not permitted"
                    )

                db.execute("""
                    CREATE TABLE IF NOT EXISTS review_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT NOT NULL UNIQUE,
                        event_id INTEGER NOT NULL
                            REFERENCES opportunity_events(id),
                        from_state TEXT NOT NULL,
                        to_state TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        note TEXT NOT NULL,
                        changed_at REAL NOT NULL
                    )
                """)

                updated = db.execute("""
                    UPDATE opportunity_events
                    SET review_state=?
                    WHERE id=? AND review_state=?
                """, (
                    new_state,
                    event_id,
                    expected_state,
                ))

                if updated.rowcount != 1:
                    raise ReviewError(
                        "Concurrent review-state conflict"
                    )

                db.execute("""
                    INSERT INTO review_history
                    (request_id, event_id, from_state,
                     to_state, actor, note, changed_at)
                    VALUES (?,?,?,?,?,?,?)
                """, (
                    request_id,
                    event_id,
                    expected_state,
                    new_state,
                    actor,
                    note,
                    time.time(),
                ))

                db.commit()

            except BaseException:
                db.rollback()
                raise

        return {
            **_safety(),
            "status": "updated",
            "event_id": event_id,
            "review_state": new_state,
            "request_id": request_id,
        }

    except sqlite3.Error as exc:
        raise ReviewError(
            "Review transition could not be recorded"
        ) from exc


def main():
    parser = argparse.ArgumentParser(
        description="R10.0B read-only opportunity review queue"
    )
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--state", choices=STATES)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    try:
        output = list_reviews(
            args.ledger,
            state=args.state,
            limit=args.limit,
        )
    except ReviewError as exc:
        parser.error(str(exc))

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

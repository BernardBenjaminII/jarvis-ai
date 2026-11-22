"""R9.22E2: offline, read-only HackerOne catalog comparison."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from .hackerone import decode, next_page, DiscoveryError


SCHEMA = "jarvis.bounty.catalog_changes.r922e2"

MATERIAL_FIELDS = (
    "name",
    "reward_status",
    "submission_state",
    "visibility",
    "currency",
    "policy_sha256",
)


class SnapshotError(ValueError):
    pass


def default_path():
    root = Path(os.environ.get(
        "JARVIS_RUNTIME_ROOT",
        str(Path.home() / ".local/share/jarvis"),
    )).expanduser()

    return root / "bounty_catalog/r4.sqlite"


def result(status, **details):
    return {
        "schema": SCHEMA,
        "status": status,
        "mode": "offline_read_only",
        "network_requests": 0,
        "testing_authorized": False,
        "execution_authorized": False,
        "notification_authorized": False,
        "alerts_issued": 0,
        "events": [],
        "event_count": 0,
        **details,
    }


def validated_snapshot(db, run_id):
    """Reject corrupt, incomplete or inconsistent stored pages."""

    pages = db.execute(
        """
        SELECT number, raw, sha256
        FROM pages
        WHERE run=?
        ORDER BY number
        """,
        (run_id,),
    ).fetchall()

    if not pages:
        raise SnapshotError("Complete run has no pages")

    records = {}

    for expected, page in enumerate(pages, start=1):
        if page["number"] != expected:
            raise SnapshotError("Catalog page sequence invalid")

        raw = page["raw"]

        if hashlib.sha256(raw).hexdigest() != page["sha256"]:
            raise SnapshotError("Catalog page checksum mismatch")

        try:
            rows, link = decode(raw)
            following = next_page(link, expected)
        except DiscoveryError as exc:
            raise SnapshotError(
                "Stored catalog page invalid"
            ) from exc

        if expected < len(pages):
            if following != expected + 1:
                raise SnapshotError(
                    "Catalog pagination chain incomplete"
                )
        elif following is not None:
            raise SnapshotError(
                "Complete run still advertises more pages"
            )

        for row in rows:
            handle = row["handle"]

            if handle in records:
                raise SnapshotError(
                    "Duplicate catalog program handle"
                )

            policy = " ".join(
                (row.get("policy_text") or "").split()
            )

            records[handle] = {
                "name": row["name"],
                "reward_status": row["reward_status"],
                "submission_state": row["submission_state"],
                "visibility": row["visibility"],
                "currency": row["currency"],
                "policy_sha256": hashlib.sha256(
                    policy.encode("utf-8")
                ).hexdigest(),
            }

    observed_handles = {
        row["handle"]
        for row in db.execute(
            "SELECT handle FROM observations WHERE run=?",
            (run_id,),
        )
    }

    if observed_handles != set(records):
        raise SnapshotError(
            "Catalog observations do not match stored pages"
        )

    return records


def compare_records(previous, current):
    events = []

    for handle in sorted(set(previous) | set(current)):
        before = previous.get(handle)
        after = current.get(handle)

        if before is None:
            event_type = "new_listing"
            changes = []
        elif after is None:
            event_type = "no_longer_listed"
            changes = []
        else:
            changes = [
                field for field in MATERIAL_FIELDS
                if before[field] != after[field]
            ]

            if not changes:
                continue

            event_type = "listing_changed"

        details = after if after is not None else before

        events.append({
            "type": event_type,
            "handle": handle,
            "program": details["name"],
            "program_url": "https://hackerone.com/" + handle,
            "changed_fields": changes,
            "human_review_required": True,
            "testing_authorized": False,
        })

    return events


def compare_catalog(path=None):
    path = Path(path or default_path()).expanduser()

    if path.is_symlink():
        raise SnapshotError("Catalog symlink forbidden")

    if not path.exists():
        return result("catalog_missing")

    if not path.is_file():
        raise SnapshotError("Catalog is not a regular file")

    uri = path.resolve(strict=True).as_uri() + "?mode=ro"

    try:
        with closing(sqlite3.connect(
            uri, uri=True, timeout=10
        )) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")

            latest = db.execute(
                """
                SELECT id, status
                FROM runs
                WHERE source='hackerone-api'
                ORDER BY finished DESC, rowid DESC
                LIMIT 1
                """
            ).fetchone()

            if latest is None:
                return result("catalog_empty")

            if latest["status"] != "complete":
                return result(
                    "blocked_latest_run_incomplete",
                    latest_run_id=latest["id"],
                    latest_run_status=latest["status"],
                )

            complete = db.execute(
                """
                SELECT id
                FROM runs
                WHERE source='hackerone-api'
                  AND status='complete'
                ORDER BY finished DESC, rowid DESC
                LIMIT 2
                """
            ).fetchall()

            if not complete or complete[0]["id"] != latest["id"]:
                raise SnapshotError(
                    "Catalog run ordering inconsistent"
                )

            current = validated_snapshot(db, latest["id"])

            if len(complete) == 1:
                return result(
                    "baseline_established",
                    baseline_run_id=latest["id"],
                    current_program_count=len(current),
                )

            previous_id = complete[1]["id"]
            previous = validated_snapshot(db, previous_id)

            events = compare_records(previous, current)

            counts = {
                kind: sum(
                    event["type"] == kind
                    for event in events
                )
                for kind in (
                    "new_listing",
                    "listing_changed",
                    "no_longer_listed",
                )
            }

            return result(
                "compared",
                previous_run_id=previous_id,
                current_run_id=latest["id"],
                previous_program_count=len(previous),
                current_program_count=len(current),
                change_counts=counts,
                events=events,
                event_count=len(events),
            )

    except sqlite3.Error as exc:
        raise SnapshotError(
            "Catalog database unavailable or invalid"
        ) from exc


def main():
    parser = argparse.ArgumentParser(
        description="Read-only HackerOne catalog change detection"
    )
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()

    try:
        output = compare_catalog(args.db)
    except SnapshotError as exc:
        parser.error(str(exc))

    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

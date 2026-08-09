"""Audit or recover the longest certified Executive Timeline prefix."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

from core.executive.timeline import (
    ExecutiveTimelineEngine,
    TimelineEvent,
)
from core.executive.timeline.serializers import TimelineEventSerializer


def read_events(path: Path) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for number, line in enumerate(
        path.read_bytes().splitlines(),
        1,
    ):
        try:
            events.append(TimelineEventSerializer.loads(line))
        except Exception as exc:
            raise RuntimeError(
                f"Cannot deserialize line {number}: {exc}"
            ) from exc
    return events


def certified_prefix(
    events: list[TimelineEvent],
) -> tuple[list[TimelineEvent], str | None]:
    accepted: list[TimelineEvent] = []

    for event in events:
        try:
            ExecutiveTimelineEngine(
                initial_events=tuple(accepted + [event])
            )
        except Exception as exc:
            return accepted, str(exc)
        accepted.append(event)

    return accepted, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("timeline_file", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Back up the file and truncate to the certified prefix.",
    )
    args = parser.parse_args()

    path = args.timeline_file.expanduser().resolve()
    events = read_events(path)
    prefix, finding = certified_prefix(events)

    print(f"File             : {path}")
    print(f"Total records    : {len(events)}")
    print(f"Certified prefix : {len(prefix)}")
    print(f"Finding          : {finding or 'none'}")

    if finding is None:
        print("[PASS] Entire timeline is certified")
        return 0

    if not args.apply:
        print("[INFO] Dry run only; use --apply to recover")
        return 2

    stamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    backup = path.with_name(
        f"{path.name}.corrupt.{stamp}"
    )
    shutil.copy2(path, backup)

    with path.open("wb") as handle:
        for event in prefix:
            handle.write(TimelineEventSerializer.dump_line(event))

    print(f"Backup           : {backup}")
    print("[PASS] Timeline truncated to certified prefix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

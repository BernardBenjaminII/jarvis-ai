#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.executive.timeline import (
    ExecutiveTimelineEngine,
    ExecutiveTimelineRepository,
    TimelineContext,
    TimelineEventDraft,
    TimelineEventKind,
    TimelineSubsystem,
)

BASE = datetime(2026, 7, 22, 10, 30, tzinfo=timezone.utc)


def main() -> int:
    engine = ExecutiveTimelineEngine(event_id_factory=lambda n: f"demo-event-{n:04d}")
    definitions = (
        (TimelineSubsystem.EXECUTIVE, TimelineEventKind.EXECUTIVE_BOOT_COMPLETED, {"state": "ready"}),
        (TimelineSubsystem.MISSION, TimelineEventKind.MISSION_STARTED, {"title": "Certify persistent history"}),
        (TimelineSubsystem.OBSERVATION, TimelineEventKind.OBSERVATION_RECEIVED, {"finding": "timeline available"}),
        (TimelineSubsystem.REASONING, TimelineEventKind.HYPOTHESIS_SELECTED, {"confidence": 0.94}),
        (TimelineSubsystem.PERSISTENCE, TimelineEventKind.CHECKPOINT_CREATED, {"checkpoint_id": "checkpoint-0044"}),
    )
    for offset, (subsystem, kind, payload) in enumerate(definitions):
        engine.append(
            TimelineEventDraft(
                subsystem=subsystem,
                kind=kind,
                context=TimelineContext(
                    session_id="executive-session-demo",
                    mission_id="mission-persistence-001",
                ),
                payload=payload,
                occurred_at=BASE + timedelta(seconds=offset),
            )
        )

    with TemporaryDirectory(prefix="jarvis-a68-") as root:
        repository = ExecutiveTimelineRepository(root)
        repository.append_many(engine.events)
        restored = ExecutiveTimelineRepository(root)
        report = restored.verify()
        stats = restored.statistics()

        print("=" * 88)
        print("GENESIS VI-A6.8 PART A — PERSISTENT EXECUTIVE TIMELINE")
        print("=" * 88)
        print(f"Storage path          : {restored.storage_path}")
        print(f"Persisted events      : {stats.event_count}")
        print(f"Sessions indexed      : {stats.session_count}")
        print(f"Missions indexed      : {stats.mission_count}")
        print(f"Storage bytes         : {stats.storage_bytes}")
        print(f"Integrity certified   : {report.certified}")
        print(f"Terminal fingerprint  : {report.terminal_fingerprint}")
        print(f"Report fingerprint    : {report.report_fingerprint}")
        print("\nMISSION HISTORY")
        for event in restored.load_mission("mission-persistence-001"):
            print(f"{event.sequence:03d} {event.subsystem.value:<12} {event.kind.value}")
        print("\nGENESIS VI-A6.8 PART A TEST DRIVE COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

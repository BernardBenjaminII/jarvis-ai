from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.executive.timeline import (
    AppendOnlyTimelineStorage,
    ExecutiveTimelineEngine,
    ExecutiveTimelineRepository,
    RepositoryIntegrityStatus,
    TimelineContext,
    TimelineEventDraft,
    TimelineEventKind,
    TimelineEventSerializer,
    TimelineRepositoryConflictError,
    TimelineRepositoryStorageError,
    TimelineSubsystem,
)

NOW = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)


def build_events():
    engine = ExecutiveTimelineEngine(event_id_factory=lambda n: f"event-{n:04d}")
    engine.append(
        TimelineEventDraft(
            subsystem=TimelineSubsystem.EXECUTIVE,
            kind=TimelineEventKind.EXECUTIVE_BOOT_STARTED,
            context=TimelineContext(session_id="session-a"),
            payload={"state": "booting"},
            occurred_at=NOW,
        )
    )
    engine.append(
        TimelineEventDraft(
            subsystem=TimelineSubsystem.MISSION,
            kind=TimelineEventKind.MISSION_STARTED,
            context=TimelineContext(session_id="session-a", mission_id="mission-a"),
            payload={"title": "Repository certification"},
            occurred_at=NOW,
        )
    )
    engine.append(
        TimelineEventDraft(
            subsystem=TimelineSubsystem.REASONING,
            kind=TimelineEventKind.HYPOTHESIS_SELECTED,
            context=TimelineContext(session_id="session-a", mission_id="mission-a"),
            payload={"confidence": 0.91},
            occurred_at=NOW,
        )
    )
    return engine.events


class GenesisVIA68PartATests(unittest.TestCase):
    def test_serializer_round_trip(self):
        event = build_events()[0]
        self.assertEqual(TimelineEventSerializer.loads(TimelineEventSerializer.dumps(event)), event)

    def test_serializer_is_deterministic(self):
        event = build_events()[1]
        self.assertEqual(TimelineEventSerializer.dumps(event), TimelineEventSerializer.dumps(event))

    def test_storage_rejects_path_escape(self):
        with TemporaryDirectory() as root:
            with self.assertRaises(TimelineRepositoryStorageError):
                AppendOnlyTimelineStorage(root, filename="../escape.jsonl")

    def test_repository_append_and_reload(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            restored = ExecutiveTimelineRepository(root)
            self.assertEqual(restored.events, build_events())

    def test_repository_is_append_only(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            events = build_events()
            repo.append_many(events)
            with self.assertRaises(TimelineRepositoryConflictError):
                repo.append(events[0])

    def test_repository_rejects_sequence_gap(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            with self.assertRaises(TimelineRepositoryConflictError):
                repo.append(build_events()[1])

    def test_get_by_event_id(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            self.assertEqual(repo.get("event-0002").sequence, 2)
            self.assertIsNone(repo.get("missing"))

    def test_session_index(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            self.assertEqual(len(repo.load_session("session-a")), 3)

    def test_mission_index(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            self.assertEqual([e.sequence for e in repo.load_mission("mission-a")], [2, 3])

    def test_latest_is_newest_first(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            self.assertEqual([e.sequence for e in repo.latest(2)], [3, 2])

    def test_statistics_are_certified(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            stats = repo.statistics()
            self.assertEqual(stats.event_count, 3)
            self.assertEqual(stats.session_count, 1)
            self.assertEqual(stats.mission_count, 1)
            self.assertTrue(stats.verify_fingerprint())

    def test_integrity_report_is_certified(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            report = repo.verify()
            self.assertEqual(report.status, RepositoryIntegrityStatus.CERTIFIED)
            self.assertTrue(report.verify_fingerprint())

    def test_event_contract_remains_immutable(self):
        event = build_events()[0]
        with self.assertRaises(FrozenInstanceError):
            event.sequence = 99

    def test_index_contract_is_immutable(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            repo.append_many(build_events())
            with self.assertRaises(TypeError):
                repo.indexes.by_event_id["x"] = 9

    def test_empty_repository_is_certified(self):
        with TemporaryDirectory() as root:
            repo = ExecutiveTimelineRepository(root)
            self.assertTrue(repo.verify().certified)
            self.assertEqual(repo.statistics().event_count, 0)


if __name__ == "__main__":
    unittest.main()

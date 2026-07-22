from __future__ import annotations
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from core.executive.timeline import InvalidQueryError, TimelineQueryEngine, assess_replay_readiness

@dataclass(frozen=True)
class Event:
    event_id: str
    sequence: int
    timestamp: datetime
    mission_id: str
    session_id: str
    subsystem: str
    event_kind: str

class Repository:
    def __init__(self, events): self._events = tuple(events)
    def __iter__(self): return iter(self._events)

def fixture_repository():
    base = datetime(2026, 7, 22, 8, 0, tzinfo=timezone.utc)
    return Repository((
        Event("e3", 3, base.replace(minute=3), "m2", "s2", "recovery", "recovered"),
        Event("e1", 1, base.replace(minute=1), "m1", "s1", "lifecycle", "started"),
        Event("e2", 2, base.replace(minute=2), "m1", "s1", "reasoning", "inference"),
        Event("e4", 4, base.replace(minute=4), "m2", "s2", "checkpoint", "checkpoint"),
        Event("e5", 5, base.replace(minute=5), "m2", "s2", "lifecycle", "completed"),
    ))

class GenesisVIA68PartBTests(unittest.TestCase):
    def setUp(self): self.engine = TimelineQueryEngine(fixture_repository())
    def test_order(self): self.assertEqual([e.sequence for e in self.engine.all()], [1,2,3,4,5])
    def test_latest(self): self.assertEqual([e.sequence for e in self.engine.latest(2)], [4,5])
    def test_mission(self): self.assertEqual(len(self.engine.by_mission("m1")), 2)
    def test_session(self): self.assertEqual(len(self.engine.by_session("s2")), 3)
    def test_subsystem(self): self.assertEqual([e.sequence for e in self.engine.by_subsystem("lifecycle")], [1,5])
    def test_kind(self): self.assertEqual(self.engine.by_event_kind("checkpoint")[0].sequence, 4)
    def test_sequence_range(self): self.assertEqual([e.sequence for e in self.engine.sequence_range(2,4)], [2,3,4])
    def test_time_range(self): self.assertEqual([e.sequence for e in self.engine.between("2026-07-22T08:02:00+00:00","2026-07-22T08:04:00+00:00")], [2,3,4])
    def test_page(self):
        page = self.engine.page(offset=1, limit=2)
        self.assertEqual([e.sequence for e in page.items], [2,3]); self.assertTrue(page.has_next)
    def test_statistics(self):
        stats = self.engine.statistics(); self.assertEqual(stats.total_events, 5); self.assertEqual(dict(stats.missions), {"m1":2,"m2":3})
    def test_fingerprint(self): self.assertEqual(self.engine.fingerprint(), self.engine.fingerprint())
    def test_replay_ready(self): self.assertTrue(assess_replay_readiness(fixture_repository()).ready)
    def test_bad_page(self):
        with self.assertRaises(InvalidQueryError): self.engine.page(offset=-1)
    def test_bad_range(self):
        with self.assertRaises(InvalidQueryError): self.engine.sequence_range(5,2)
    def test_immutable_results(self): self.assertIsInstance(self.engine.all(), tuple)

if __name__ == "__main__": unittest.main()

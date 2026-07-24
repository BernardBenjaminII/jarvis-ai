from dataclasses import replace
from datetime import datetime, timezone
import unittest
from core.executive.timeline import *

T = datetime(2026, 7, 22, 8, 0, tzinfo=timezone.utc)

def d(kind, subsystem=TimelineSubsystem.EXECUTIVE, mission="m1", parent=None, payload=None):
    return TimelineEventDraft(
        subsystem=subsystem, kind=kind,
        context=TimelineContext(session_id="s1", mission_id=mission),
        payload=payload or {}, parent_event_id=parent, occurred_at=T,
    )

class Tests(unittest.TestCase):
    def engine(self):
        return ExecutiveTimelineEngine(event_id_factory=lambda n: f"event-{n:04d}")

    def test_genesis(self):
        e = self.engine(); x = e.append(d(TimelineEventKind.EXECUTIVE_BOOT_STARTED))
        self.assertEqual(x.previous_event_fingerprint, "0" * 64)

    def test_chain(self):
        e = self.engine()
        a = e.append(d(TimelineEventKind.EXECUTIVE_BOOT_STARTED))
        b = e.append(d(TimelineEventKind.EXECUTIVE_BOOT_COMPLETED))
        self.assertEqual(b.previous_event_fingerprint, a.event_fingerprint)

    def test_sequence(self):
        e = self.engine()
        e.append_many([d(TimelineEventKind.EXECUTIVE_BOOT_STARTED), d(TimelineEventKind.EXECUTIVE_BOOT_COMPLETED)])
        self.assertEqual([x.sequence for x in e.events], [1, 2])

    def test_deterministic(self):
        a = self.engine().append(d(TimelineEventKind.MISSION_STARTED))
        b = self.engine().append(d(TimelineEventKind.MISSION_STARTED))
        self.assertEqual(a.event_fingerprint, b.event_fingerprint)

    def test_valid(self):
        e = self.engine(); e.append(d(TimelineEventKind.MISSION_STARTED))
        self.assertTrue(e.verify().certified)

    def test_payload_tamper(self):
        e = self.engine(); e.append(d(TimelineEventKind.NOTE_RECORDED, payload={"x": 1}))
        e._events[0] = replace(e._events[0], payload={"x": 2})
        self.assertFalse(e.verify().certified)

    def test_chain_tamper(self):
        e = self.engine(); e.append_many([d(TimelineEventKind.MISSION_STARTED), d(TimelineEventKind.MISSION_COMPLETED)])
        e._events[1] = replace(e._events[1], previous_event_fingerprint="f" * 64)
        self.assertFalse(e.verify().certified)

    def test_parent(self):
        e = self.engine()
        with self.assertRaises(InvalidTimelineEventError):
            e.append(d(TimelineEventKind.DECISION_CERTIFIED, parent="missing"))

    def test_subsystem_query(self):
        e = self.engine()
        e.append(d(TimelineEventKind.OBSERVATION_RECEIVED, TimelineSubsystem.OBSERVATION))
        e.append(d(TimelineEventKind.REASONING_STARTED, TimelineSubsystem.REASONING))
        self.assertEqual(len(e.query(TimelineQuery(subsystem=TimelineSubsystem.REASONING))), 1)

    def test_mission_query(self):
        e = self.engine()
        e.append(d(TimelineEventKind.MISSION_STARTED, mission="a"))
        e.append(d(TimelineEventKind.MISSION_STARTED, mission="b"))
        self.assertEqual(e.query(TimelineQuery(mission_id="b"))[0].context.mission_id, "b")

    def test_latest(self):
        e = self.engine()
        e.append_many([d(TimelineEventKind.MISSION_CREATED), d(TimelineEventKind.MISSION_STARTED), d(TimelineEventKind.MISSION_COMPLETED)])
        self.assertEqual([x.sequence for x in e.latest(2)], [3, 2])

    def test_report_deterministic(self):
        e = self.engine(); e.append(d(TimelineEventKind.MISSION_STARTED))
        self.assertEqual(e.verify().report_fingerprint, e.verify().report_fingerprint)

    def test_empty(self):
        self.assertTrue(self.engine().verify().certified)

    def test_duplicate_id(self):
        e = ExecutiveTimelineEngine(event_id_factory=lambda n: "same")
        e.append(d(TimelineEventKind.MISSION_STARTED))
        with self.assertRaises(InvalidTimelineEventError):
            e.append(d(TimelineEventKind.MISSION_COMPLETED))

if __name__ == "__main__":
    unittest.main()

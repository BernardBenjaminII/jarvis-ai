"""Tests for Genesis VI-A5 executive session."""
from __future__ import annotations
import unittest
from datetime import datetime, timedelta, timezone
from core.cognition import (
    CognitiveState, ExecutiveSession, ExecutiveSessionStatus,
    MemoryEntry, MemoryEntryKind,
)

class Clock:
    def __init__(self): self.value=datetime(2026,1,1,tzinfo=timezone.utc)
    def __call__(self):
        value=self.value; self.value += timedelta(seconds=1); return value

def make_session():
    return ExecutiveSession(
        session_id="session-001", mission_id="mission-001",
        executive_id="jarvis-executive", authority="commander", clock=Clock(),
    )

class ExecutiveSessionTests(unittest.TestCase):
    def test_creation_has_stable_identity(self):
        session=make_session(); snap=session.snapshot()
        self.assertEqual(snap.session_id,"session-001")
        self.assertEqual(snap.executive_id,"jarvis-executive")
        self.assertIs(snap.status,ExecutiveSessionStatus.CREATED)

    def test_cycle_inherits_mission_and_authority(self):
        session=make_session()
        context=session.create_cycle(cycle_id="cycle-001",goal="Observe mission.")
        self.assertEqual(context.mission_id,"mission-001")
        self.assertEqual(context.authority,"commander")

    def test_duplicate_cycle_rejected(self):
        session=make_session(); session.create_cycle(cycle_id="cycle-001",goal="One")
        with self.assertRaises(ValueError): session.create_cycle(cycle_id="cycle-001",goal="Two")

    def test_only_one_cycle_may_be_active(self):
        session=make_session()
        session.create_cycle(cycle_id="a",goal="A")
        session.create_cycle(cycle_id="b",goal="B")
        session.start_cycle("a")
        with self.assertRaises(RuntimeError): session.start_cycle("b")

    def test_session_drives_cycle(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A")
        session.start_cycle("a")
        context=session.advance_cycle("a",CognitiveState.OBSERVING,reason="Observe")
        self.assertIs(context.state,CognitiveState.OBSERVING)
        self.assertEqual(session.active_cycle_id,"a")

    def test_session_admits_memory(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A")
        session.start_cycle("a")
        session.admit_memory("a",MemoryEntry(entry_id="goal",kind=MemoryEntryKind.GOAL,content="A"))
        self.assertEqual(session.cycle_snapshot("a").context.working_memory[0].entry_id,"goal")

    def test_suspend_releases_active_slot(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A")
        session.start_cycle("a"); session.suspend_cycle("a",reason="Pause")
        self.assertIsNone(session.active_cycle_id)
        self.assertIs(session.status,ExecutiveSessionStatus.SUSPENDED)

    def test_completed_cycle_remains_in_history(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A")
        session.start_cycle("a")
        for state in (CognitiveState.OBSERVING,CognitiveState.ATTENDING,CognitiveState.REASONING,CognitiveState.EVALUATING,CognitiveState.PLANNING,CognitiveState.EXECUTING,CognitiveState.REFLECTING):
            session.advance_cycle("a",state,reason=state.value)
        session.complete_cycle("a")
        snap=session.snapshot()
        self.assertIsNone(snap.active_cycle_id)
        self.assertEqual(len(snap.cycles),1)
        self.assertIs(snap.cycles[0].context.state,CognitiveState.COMPLETED)

    def test_close_requires_no_active_cycle(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A"); session.start_cycle("a")
        with self.assertRaises(RuntimeError): session.close()

    def test_closed_session_rejects_new_cycle(self):
        session=make_session(); session.close()
        with self.assertRaises(RuntimeError): session.create_cycle(cycle_id="a",goal="A")

    def test_snapshot_cycles_are_sorted(self):
        session=make_session()
        session.create_cycle(cycle_id="z",goal="Z"); session.create_cycle(cycle_id="a",goal="A")
        self.assertEqual(tuple(x.context.cycle_id for x in session.snapshot().cycles),("a","z"))

    def test_event_stream_is_monotonic(self):
        session=make_session(); session.create_cycle(cycle_id="a",goal="A"); session.start_cycle("a")
        events=session.snapshot().events
        self.assertEqual(tuple(e.sequence for e in events),tuple(range(1,len(events)+1)))
        self.assertEqual(tuple(sorted(e.occurred_at for e in events)),tuple(e.occurred_at for e in events))

if __name__ == '__main__': unittest.main()

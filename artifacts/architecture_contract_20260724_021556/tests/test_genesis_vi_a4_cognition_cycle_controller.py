from __future__ import annotations
import unittest
from datetime import datetime,timedelta,timezone
from core.cognition import *
class Clock:
    def __init__(self): self.v=datetime(2026,1,1,tzinfo=timezone.utc)
    def __call__(self): x=self.v; self.v+=timedelta(seconds=1); return x
def cycle(cap=4): return CognitionCycleController(cycle_id='c1',mission_id='m1',goal='certify',authority='commander',memory_capacity=cap,clock=Clock())
class Tests(unittest.TestCase):
    def test_created(self):
        c=cycle(); self.assertIs(c.current_state,CognitiveState.IDLE); self.assertIs(c.status,CognitiveCycleStatus.CREATED)
    def test_start(self): self.assertIs(cycle().start().state,CognitiveState.INITIALIZING)
    def test_advance_requires_active(self):
        with self.assertRaises(CognitionCycleNotActiveError): cycle().advance(CognitiveState.OBSERVING,reason='x')
    def test_complete_path(self):
        c=cycle(); c.start()
        for s in (CognitiveState.OBSERVING,CognitiveState.ATTENDING,CognitiveState.REASONING,CognitiveState.EVALUATING,CognitiveState.PLANNING,CognitiveState.EXECUTING,CognitiveState.REFLECTING): c.advance(s,reason=s.value)
        self.assertIs(c.complete().status,CognitiveCycleStatus.COMPLETED)
    def test_memory(self):
        c=cycle(); c.start(); e=MemoryEntry(entry_id='g',kind=MemoryEntryKind.GOAL,content='goal'); self.assertIsNone(c.admit_memory(e)); self.assertEqual(c.context.working_memory,(e,))
    def test_eviction(self):
        c=cycle(1); c.start(); a=MemoryEntry(entry_id='a',kind=MemoryEntryKind.ASSUMPTION,content='a',importance=.1,confidence=.1); b=MemoryEntry(entry_id='b',kind=MemoryEntryKind.EVIDENCE,content='b',importance=1,confidence=1); c.admit_memory(a); self.assertEqual(c.admit_memory(b),a)
    def test_note(self):
        c=cycle(); c.start(); self.assertEqual(c.record_note('note').notes,('note',))
    def test_suspend_resume(self):
        c=cycle(); c.start(); c.advance(CognitiveState.OBSERVING,reason='o'); self.assertIs(c.suspend(reason='s').status,CognitiveCycleStatus.SUSPENDED); self.assertIs(c.start(reason='r').state,CognitiveState.INITIALIZING)
    def test_failure_closes(self):
        c=cycle(); c.start(); c.fail(reason='f'); self.assertTrue(c.is_closed)
        with self.assertRaises(CognitionCycleClosedError): c.record_note('x')
    def test_complete_requires_reflection(self):
        c=cycle(); c.start()
        with self.assertRaises(CognitionCycleNotActiveError): c.complete()
    def test_snapshot_consistent(self):
        c=cycle(); c.start(); s=c.snapshot(); self.assertEqual(s.context.events,s.state_machine.events); self.assertEqual(s.context.transitions,s.state_machine.transitions)
if __name__=='__main__': unittest.main()

"""Authoritative cognition-cycle aggregate for Genesis VI-A4."""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Iterable
from .enums import CognitiveCycleStatus, CognitiveEventKind, CognitiveState
from .errors import CognitionCycleClosedError, CognitionCycleNotActiveError
from .models import CognitiveEvent, ExecutiveContext, MemoryEntry, utc_now
from .state_machine import DEFAULT_TRANSITION_POLICY, CognitiveStateMachine, StateMachineSnapshot, TransitionPolicy
from .working_memory import WorkingMemory, WorkingMemorySnapshot

_ACTIVE=frozenset({CognitiveState.INITIALIZING,CognitiveState.OBSERVING,CognitiveState.ATTENDING,CognitiveState.RETRIEVING,CognitiveState.REASONING,CognitiveState.EVALUATING,CognitiveState.PLANNING,CognitiveState.AWAITING_AUTHORITY,CognitiveState.EXECUTING,CognitiveState.REFLECTING})
_CLOSED=frozenset({CognitiveCycleStatus.COMPLETED,CognitiveCycleStatus.FAILED})

@dataclass(frozen=True, slots=True)
class CognitionCycleSnapshot:
    context: ExecutiveContext
    working_memory: WorkingMemorySnapshot
    state_machine: StateMachineSnapshot
    def __post_init__(self)->None:
        if self.context.state is not self.state_machine.current_state: raise ValueError('context and state-machine state mismatch')
        if self.context.working_memory != self.working_memory.entries: raise ValueError('context and working-memory mismatch')
        if self.context.transitions != self.state_machine.transitions: raise ValueError('context and transition history mismatch')
        if self.context.events != self.state_machine.events: raise ValueError('context and aggregate event history mismatch')

class CognitionCycleController:
    """Own context, working memory, and lifecycle state as one aggregate."""
    def __init__(self,*,cycle_id:str,mission_id:str,goal:str,authority:str,objective_id:str|None=None,task_id:str|None=None,constraints:Iterable[str]=(),memory_capacity:int=32,policy:TransitionPolicy=DEFAULT_TRANSITION_POLICY,clock:Callable[[],datetime]=utc_now)->None:
        self._clock=clock; self._memory=WorkingMemory(memory_capacity); self._machine=CognitiveStateMachine(policy=policy,clock=clock); self._notes=[]
        now=clock(); event=CognitiveEvent(sequence=1,kind=CognitiveEventKind.CONTEXT_CREATED,message=f'Created cognition cycle {cycle_id}.',state=CognitiveState.IDLE,occurred_at=now,metadata={'cycle_id':cycle_id,'mission_id':mission_id})
        self._cycle_events=[event]
        self._context=ExecutiveContext(cycle_id=cycle_id,mission_id=mission_id,goal=goal,state=CognitiveState.IDLE,status=CognitiveCycleStatus.CREATED,authority=authority,objective_id=objective_id,task_id=task_id,constraints=tuple(constraints),events=(event,),created_at=now,updated_at=now)
    @property
    def context(self): return self._context
    @property
    def current_state(self): return self._machine.current_state
    @property
    def status(self): return self._context.status
    @property
    def is_closed(self): return self.status in _CLOSED
    @property
    def is_active(self): return self.status is CognitiveCycleStatus.ACTIVE
    @property
    def memory(self): return self._memory.snapshot()
    def _open(self):
        if self.is_closed: raise CognitionCycleClosedError(f'cognition cycle is closed: {self._context.cycle_id}')
    def _active(self):
        if not self.is_active: raise CognitionCycleNotActiveError(f'operation requires active cycle: {self._context.cycle_id}')
    @staticmethod
    def _status(state):
        if state in _ACTIVE: return CognitiveCycleStatus.ACTIVE
        if state is CognitiveState.COMPLETED: return CognitiveCycleStatus.COMPLETED
        if state is CognitiveState.FAILED: return CognitiveCycleStatus.FAILED
        if state is CognitiveState.SUSPENDED: return CognitiveCycleStatus.SUSPENDED
        return CognitiveCycleStatus.CREATED
    def _project(self):
        merged=sorted((*self._cycle_events,*self._machine.events()),key=lambda e:(e.occurred_at,e.sequence,e.kind.value))
        events=tuple(replace(e,sequence=i) for i,e in enumerate(merged,1))
        self._context=replace(self._context,state=self.current_state,status=self._status(self.current_state),working_memory=self._memory.entries(),transitions=self._machine.transitions(),events=events,notes=tuple(self._notes),updated_at=self._clock())
        return self._context
    def start(self,*,reason='Begin cognition cycle.'):
        self._open()
        if self.status not in {CognitiveCycleStatus.CREATED,CognitiveCycleStatus.SUSPENDED}: raise CognitionCycleNotActiveError('cycle can start only from created or suspended status')
        self._machine.transition_to(CognitiveState.INITIALIZING,reason=reason); return self._project()
    def advance(self,next_state:CognitiveState,*,reason:str):
        self._open(); self._active(); self._machine.transition_to(next_state,reason=reason); return self._project()
    def admit_memory(self,entry:MemoryEntry):
        self._open(); self._active(); evicted=self._memory.admit(entry); now=self._clock()
        self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.MEMORY_ADMITTED,message=f'Admitted working-memory entry {entry.entry_id}.',state=self.current_state,occurred_at=now,metadata={'entry_id':entry.entry_id,'kind':entry.kind.value}))
        if evicted is not None: self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.MEMORY_EVICTED,message=f'Evicted working-memory entry {evicted.entry_id}.',state=self.current_state,occurred_at=now,metadata={'entry_id':evicted.entry_id,'replacement_id':entry.entry_id}))
        self._project(); return evicted
    def record_note(self,note:str):
        self._open(); self._active()
        if not note.strip(): raise ValueError('note must not be empty')
        self._notes.append(note); self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.NOTE_RECORDED,message=note,state=self.current_state,occurred_at=self._clock(),metadata={'note_index':len(self._notes)})); return self._project()
    def suspend(self,*,reason:str):
        self._open(); self._active(); self._machine.transition_to(CognitiveState.SUSPENDED,reason=reason); self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.CYCLE_SUSPENDED,message=reason,state=CognitiveState.SUSPENDED,occurred_at=self._clock(),metadata={'cycle_id':self._context.cycle_id})); return self._project()
    def fail(self,*,reason:str):
        self._open()
        if self.status not in {CognitiveCycleStatus.ACTIVE,CognitiveCycleStatus.SUSPENDED}: raise CognitionCycleNotActiveError('only active or suspended cycles may fail')
        self._machine.transition_to(CognitiveState.FAILED,reason=reason); self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.CYCLE_FAILED,message=reason,state=CognitiveState.FAILED,occurred_at=self._clock(),metadata={'cycle_id':self._context.cycle_id})); return self._project()
    def complete(self,*,reason='Cognition cycle completed.'):
        self._open(); self._active()
        if self.current_state is not CognitiveState.REFLECTING: raise CognitionCycleNotActiveError('cycle may complete only from reflecting state')
        self._machine.transition_to(CognitiveState.COMPLETED,reason=reason); self._cycle_events.append(CognitiveEvent(sequence=len(self._cycle_events)+1,kind=CognitiveEventKind.CYCLE_COMPLETED,message=reason,state=CognitiveState.COMPLETED,occurred_at=self._clock(),metadata={'cycle_id':self._context.cycle_id})); return self._project()
    def snapshot(self):
        context=self._project(); raw=self._machine.snapshot(); aggregate=StateMachineSnapshot(current_state=raw.current_state,transitions=raw.transitions,events=context.events); return CognitionCycleSnapshot(context=context,working_memory=self._memory.snapshot(),state_machine=aggregate)

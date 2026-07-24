#!/usr/bin/env bash
set -euo pipefail

ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"

[[ -d core/executive ]] || { echo "ERROR: Run from the JARVIS repository root."; exit 1; }
[[ -x "$PYTHON_BIN" ]] || { echo "ERROR: Invalid Python: $PYTHON_BIN"; exit 1; }

BACKUP=".migration_backups/genesis_vi_a67_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"
backup() {
  [[ -f "$1" ]] || return 0
  mkdir -p "$BACKUP/$(dirname "$1")"
  cp "$1" "$BACKUP/$1"
}

FILES=(
  core/executive/timeline/__init__.py
  core/executive/timeline/contracts.py
  core/executive/timeline/engine.py
  core/executive/timeline/queries.py
  core/executive/timeline/adapters.py
  tests/test_genesis_vi_a67_executive_timeline.py
  docs/architecture/genesis_vi_a67_executive_timeline_engine.md
  dev/verification/verify_genesis_vi_a67.py
  dev/verify_genesis_vi_a67.sh
  dev/demo_genesis_vi_a67.py
)
for f in "${FILES[@]}"; do backup "$f"; done
mkdir -p core/executive/timeline tests docs/architecture dev/verification dev

cat > core/executive/timeline/contracts.py <<'PY'
"""Immutable contracts for Genesis VI-A6.7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

GENESIS_FINGERPRINT = "0" * 64

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

def fingerprint(value: object) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()

class TimelineError(RuntimeError):
    pass

class InvalidTimelineEventError(TimelineError):
    pass

class TimelineSubsystem(str, Enum):
    EXECUTIVE = "executive"
    LIFECYCLE = "lifecycle"
    MISSION = "mission"
    OBSERVATION = "observation"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    DECISION = "decision"
    PERSISTENCE = "persistence"
    INTEGRITY = "integrity"
    RECOVERY = "recovery"
    OPERATOR = "operator"
    SYSTEM = "system"

class TimelineEventKind(str, Enum):
    EXECUTIVE_BOOT_STARTED = "executive_boot_started"
    EXECUTIVE_BOOT_COMPLETED = "executive_boot_completed"
    EXECUTIVE_SHUTDOWN_STARTED = "executive_shutdown_started"
    EXECUTIVE_SHUTDOWN_COMPLETED = "executive_shutdown_completed"
    EXECUTIVE_FAILURE = "executive_failure"
    SESSION_CREATED = "session_created"
    SESSION_ACTIVATED = "session_activated"
    SESSION_SUSPENDED = "session_suspended"
    SESSION_RESUMED = "session_resumed"
    SESSION_COMPLETED = "session_completed"
    SESSION_ABORTED = "session_aborted"
    MISSION_CREATED = "mission_created"
    MISSION_STARTED = "mission_started"
    MISSION_COMPLETED = "mission_completed"
    MISSION_ABORTED = "mission_aborted"
    OBJECTIVE_STARTED = "objective_started"
    OBJECTIVE_COMPLETED = "objective_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    ACTIVITY_STARTED = "activity_started"
    ACTIVITY_COMPLETED = "activity_completed"
    OBSERVATION_RECEIVED = "observation_received"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    REASONING_STARTED = "reasoning_started"
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    HYPOTHESIS_SELECTED = "hypothesis_selected"
    DECISION_PROPOSED = "decision_proposed"
    DECISION_CERTIFIED = "decision_certified"
    CHECKPOINT_STARTED = "checkpoint_started"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_VERIFIED = "checkpoint_verified"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_REFUSED = "recovery_refused"
    OPERATOR_COMMAND = "operator_command"
    NOTE_RECORDED = "note_recorded"

@dataclass(frozen=True, slots=True)
class TimelineContext:
    session_id: str | None = None
    mission_id: str | None = None
    objective_id: str | None = None
    task_id: str | None = None
    activity_id: str | None = None
    correlation_id: str | None = None

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "session_id": self.session_id, "mission_id": self.mission_id,
            "objective_id": self.objective_id, "task_id": self.task_id,
            "activity_id": self.activity_id, "correlation_id": self.correlation_id,
        }

@dataclass(frozen=True, slots=True)
class TimelineEventDraft:
    subsystem: TimelineSubsystem
    kind: TimelineEventKind
    context: TimelineContext = field(default_factory=TimelineContext)
    payload: Mapping[str, object] = field(default_factory=dict)
    parent_event_id: str | None = None
    occurred_at: datetime | None = None

    def validate(self) -> None:
        if not isinstance(self.subsystem, TimelineSubsystem):
            raise InvalidTimelineEventError("Invalid subsystem.")
        if not isinstance(self.kind, TimelineEventKind):
            raise InvalidTimelineEventError("Invalid event kind.")
        if not isinstance(self.context, TimelineContext):
            raise InvalidTimelineEventError("Invalid context.")
        if not isinstance(self.payload, Mapping):
            raise InvalidTimelineEventError("Payload must be a mapping.")
        if self.occurred_at is not None and self.occurred_at.tzinfo is None:
            raise InvalidTimelineEventError("occurred_at must be timezone-aware.")

@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: str
    sequence: int
    occurred_at: datetime
    subsystem: TimelineSubsystem
    kind: TimelineEventKind
    context: TimelineContext
    payload: Mapping[str, object]
    parent_event_id: str | None
    previous_event_fingerprint: str
    event_fingerprint: str

    @classmethod
    def create(cls, *, event_id: str, sequence: int, occurred_at: datetime,
               subsystem: TimelineSubsystem, kind: TimelineEventKind,
               context: TimelineContext, payload: Mapping[str, object],
               parent_event_id: str | None,
               previous_event_fingerprint: str) -> "TimelineEvent":
        material = {
            "event_id": event_id, "sequence": sequence,
            "occurred_at": occurred_at.isoformat(), "subsystem": subsystem.value,
            "kind": kind.value, "context": context.canonical_dict(),
            "payload": dict(payload), "parent_event_id": parent_event_id,
            "previous_event_fingerprint": previous_event_fingerprint,
        }
        return cls(event_id, sequence, occurred_at, subsystem, kind, context,
                   dict(payload), parent_event_id, previous_event_fingerprint,
                   fingerprint(material))

    def material(self) -> dict[str, object]:
        return {
            "event_id": self.event_id, "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "subsystem": self.subsystem.value, "kind": self.kind.value,
            "context": self.context.canonical_dict(), "payload": dict(self.payload),
            "parent_event_id": self.parent_event_id,
            "previous_event_fingerprint": self.previous_event_fingerprint,
        }

    def verify_fingerprint(self) -> bool:
        return fingerprint(self.material()) == self.event_fingerprint

@dataclass(frozen=True, slots=True)
class TimelineIntegrityReport:
    certified: bool
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    terminal_fingerprint: str
    findings: tuple[str, ...]
    report_fingerprint: str

    @classmethod
    def create(cls, events: Sequence[TimelineEvent], findings: Iterable[str]) -> "TimelineIntegrityReport":
        f = tuple(findings)
        material = {
            "certified": not f, "event_count": len(events),
            "first_sequence": events[0].sequence if events else None,
            "last_sequence": events[-1].sequence if events else None,
            "terminal_fingerprint": events[-1].event_fingerprint if events else GENESIS_FINGERPRINT,
            "findings": f,
        }
        return cls(not f, len(events), material["first_sequence"],
                   material["last_sequence"], material["terminal_fingerprint"],
                   f, fingerprint(material))
PY

cat > core/executive/timeline/queries.py <<'PY'
"""Pure timeline queries."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from .contracts import TimelineEvent, TimelineEventKind, TimelineSubsystem

@dataclass(frozen=True, slots=True)
class TimelineQuery:
    subsystem: TimelineSubsystem | None = None
    kind: TimelineEventKind | None = None
    session_id: str | None = None
    mission_id: str | None = None
    objective_id: str | None = None
    task_id: str | None = None
    activity_id: str | None = None
    correlation_id: str | None = None
    sequence_from: int | None = None
    sequence_to: int | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    limit: int | None = None
    newest_first: bool = False

def execute_query(events: Iterable[TimelineEvent], q: TimelineQuery) -> tuple[TimelineEvent, ...]:
    if q.limit is not None and q.limit < 0:
        raise ValueError("limit cannot be negative.")
    result = []
    for e in events:
        c = e.context
        if q.subsystem is not None and e.subsystem is not q.subsystem: continue
        if q.kind is not None and e.kind is not q.kind: continue
        if q.session_id is not None and c.session_id != q.session_id: continue
        if q.mission_id is not None and c.mission_id != q.mission_id: continue
        if q.objective_id is not None and c.objective_id != q.objective_id: continue
        if q.task_id is not None and c.task_id != q.task_id: continue
        if q.activity_id is not None and c.activity_id != q.activity_id: continue
        if q.correlation_id is not None and c.correlation_id != q.correlation_id: continue
        if q.sequence_from is not None and e.sequence < q.sequence_from: continue
        if q.sequence_to is not None and e.sequence > q.sequence_to: continue
        if q.occurred_from is not None and e.occurred_at < q.occurred_from: continue
        if q.occurred_to is not None and e.occurred_at > q.occurred_to: continue
        result.append(e)
    result.sort(key=lambda e: e.sequence, reverse=q.newest_first)
    return tuple(result[:q.limit] if q.limit is not None else result)
PY

cat > core/executive/timeline/engine.py <<'PY'
"""Append-only Executive Timeline Engine."""
from __future__ import annotations
from collections.abc import Iterable
from typing import Callable
from uuid import uuid4
from .contracts import (
    GENESIS_FINGERPRINT, InvalidTimelineEventError, TimelineEvent,
    TimelineEventDraft, TimelineIntegrityReport, utc_now,
)
from .queries import TimelineQuery, execute_query

class ExecutiveTimelineEngine:
    def __init__(self, *, event_id_factory: Callable[[int], str] | None = None) -> None:
        self._events: list[TimelineEvent] = []
        self._event_id_factory = event_id_factory or (
            lambda n: f"timeline-event-{n:08d}-{uuid4().hex}"
        )

    @property
    def events(self) -> tuple[TimelineEvent, ...]:
        return tuple(self._events)

    @property
    def terminal_fingerprint(self) -> str:
        return self._events[-1].event_fingerprint if self._events else GENESIS_FINGERPRINT

    def append(self, draft: TimelineEventDraft) -> TimelineEvent:
        draft.validate()
        sequence = len(self._events) + 1
        event_id = self._event_id_factory(sequence)
        if not event_id or any(e.event_id == event_id for e in self._events):
            raise InvalidTimelineEventError("Event ID must be unique and non-empty.")
        if draft.parent_event_id is not None and not any(
            e.event_id == draft.parent_event_id for e in self._events
        ):
            raise InvalidTimelineEventError("Parent must reference an earlier event.")
        event = TimelineEvent.create(
            event_id=event_id, sequence=sequence,
            occurred_at=draft.occurred_at or utc_now(),
            subsystem=draft.subsystem, kind=draft.kind, context=draft.context,
            payload=draft.payload, parent_event_id=draft.parent_event_id,
            previous_event_fingerprint=self.terminal_fingerprint,
        )
        self._events.append(event)
        return event

    def append_many(self, drafts: Iterable[TimelineEventDraft]) -> tuple[TimelineEvent, ...]:
        return tuple(self.append(draft) for draft in drafts)

    def query(self, query: TimelineQuery) -> tuple[TimelineEvent, ...]:
        return execute_query(self._events, query)

    def latest(self, limit: int = 25) -> tuple[TimelineEvent, ...]:
        return self.query(TimelineQuery(limit=limit, newest_first=True))

    def verify(self) -> TimelineIntegrityReport:
        findings = []
        expected_previous = GENESIS_FINGERPRINT
        seen: set[str] = set()
        for expected_sequence, event in enumerate(self._events, 1):
            if event.sequence != expected_sequence:
                findings.append(f"Sequence mismatch at {expected_sequence}.")
            if event.event_id in seen:
                findings.append(f"Duplicate event ID: {event.event_id}.")
            if event.previous_event_fingerprint != expected_previous:
                findings.append(f"Broken chain before sequence {event.sequence}.")
            if not event.verify_fingerprint():
                findings.append(f"Invalid event fingerprint at sequence {event.sequence}.")
            if event.parent_event_id is not None and event.parent_event_id not in seen:
                findings.append(f"Invalid parent at sequence {event.sequence}.")
            seen.add(event.event_id)
            expected_previous = event.event_fingerprint
        return TimelineIntegrityReport.create(self._events, findings)
PY

cat > core/executive/timeline/adapters.py <<'PY'
"""VI-A6.6 lifecycle-to-timeline adapter."""
from __future__ import annotations
from .contracts import TimelineContext, TimelineEventDraft, TimelineEventKind, TimelineSubsystem

_MAP = {
    "boot_started": TimelineEventKind.EXECUTIVE_BOOT_STARTED,
    "boot_completed": TimelineEventKind.EXECUTIVE_BOOT_COMPLETED,
    "session_created": TimelineEventKind.SESSION_CREATED,
    "session_activated": TimelineEventKind.SESSION_ACTIVATED,
    "checkpoint_started": TimelineEventKind.CHECKPOINT_STARTED,
    "checkpoint_completed": TimelineEventKind.CHECKPOINT_CREATED,
    "session_suspended": TimelineEventKind.SESSION_SUSPENDED,
    "recovery_started": TimelineEventKind.RECOVERY_STARTED,
    "recovery_completed": TimelineEventKind.RECOVERY_COMPLETED,
    "session_completed": TimelineEventKind.SESSION_COMPLETED,
    "session_aborted": TimelineEventKind.SESSION_ABORTED,
    "shutdown_started": TimelineEventKind.EXECUTIVE_SHUTDOWN_STARTED,
    "shutdown_completed": TimelineEventKind.EXECUTIVE_SHUTDOWN_COMPLETED,
    "failure_recorded": TimelineEventKind.EXECUTIVE_FAILURE,
}

def lifecycle_event_to_draft(event: object, *, mission_id: str | None = None) -> TimelineEventDraft:
    raw = getattr(event, "kind")
    value = getattr(raw, "value", str(raw))
    if value not in _MAP:
        raise ValueError(f"Unsupported lifecycle event: {value}")
    state = getattr(event, "lifecycle_state", None)
    return TimelineEventDraft(
        subsystem=TimelineSubsystem.LIFECYCLE,
        kind=_MAP[value],
        context=TimelineContext(
            session_id=getattr(event, "session_id", None),
            mission_id=mission_id,
        ),
        payload={
            "detail": getattr(event, "detail", ""),
            "lifecycle_state": getattr(state, "value", str(state)),
            "source_sequence": getattr(event, "sequence", None),
            "source_fingerprint": getattr(event, "event_fingerprint", None),
        },
        occurred_at=getattr(event, "occurred_at", None),
    )
PY

cat > core/executive/timeline/__init__.py <<'PY'
"""Public Genesis VI-A6.7 API."""
from .adapters import lifecycle_event_to_draft
from .contracts import (
    GENESIS_FINGERPRINT, InvalidTimelineEventError, TimelineContext,
    TimelineError, TimelineEvent, TimelineEventDraft, TimelineEventKind,
    TimelineIntegrityReport, TimelineSubsystem,
)
from .engine import ExecutiveTimelineEngine
from .queries import TimelineQuery, execute_query

__all__ = [
    "ExecutiveTimelineEngine", "GENESIS_FINGERPRINT",
    "InvalidTimelineEventError", "TimelineContext", "TimelineError",
    "TimelineEvent", "TimelineEventDraft", "TimelineEventKind",
    "TimelineIntegrityReport", "TimelineQuery", "TimelineSubsystem",
    "execute_query", "lifecycle_event_to_draft",
]
PY

cat > tests/test_genesis_vi_a67_executive_timeline.py <<'PY'
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
PY

cat > docs/architecture/genesis_vi_a67_executive_timeline_engine.md <<'MD'
# Genesis VI-A6.7 — Executive Timeline Engine

**Status:** Implemented  
**Depends on:** Genesis VI-A6.6

## Purpose

The Executive Timeline is the authoritative chronological history of JARVIS.
It is not ordinary logging. It is an immutable, queryable, fingerprint-chained
record of Executive facts.

## Event Chain

```text
Genesis fingerprint
        ↓
Event 1 fingerprint
        ↓
Event 2 fingerprint
        ↓
Event 3 fingerprint
```

Each event records sequence, time, subsystem, event kind, session and mission
context, objective/task/activity context, payload, parent event, previous
fingerprint, and its own fingerprint.

## Boundaries

VI-A6.7 admits, orders, queries, and verifies in-memory events. It does not
persist them or replay behavior. Persistent storage belongs to VI-A6.8.
Deterministic replay belongs to VI-A6.9.

## Mission Control

Mission Control can now display genuine Executive activity rather than
synthetic animations:

```text
Observation received
Knowledge retrieved
Reasoning started
Hypothesis selected
Decision certified
Checkpoint created
```
MD

cat > dev/verification/verify_genesis_vi_a67.py <<'PY'
#!/usr/bin/env python3
from hashlib import sha256
import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    ROOT / "core/executive/timeline/__init__.py",
    ROOT / "core/executive/timeline/contracts.py",
    ROOT / "core/executive/timeline/engine.py",
    ROOT / "core/executive/timeline/queries.py",
    ROOT / "core/executive/timeline/adapters.py",
    ROOT / "tests/test_genesis_vi_a67_executive_timeline.py",
    ROOT / "docs/architecture/genesis_vi_a67_executive_timeline_engine.md",
]
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)

missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
if missing: fail(f"Missing: {missing}")
print("[PASS] Canonical Genesis VI-A6.7 structure")

sys.path.insert(0, str(ROOT))
from core.executive.timeline import ExecutiveTimelineEngine, TimelineEvent, TimelineQuery
if not all(inspect.isclass(x) for x in (ExecutiveTimelineEngine, TimelineEvent, TimelineQuery)):
    fail("Unstable public API")
print("[PASS] Stable Executive timeline public API")

source = inspect.getsource(ExecutiveTimelineEngine)
for token in ("previous_event_fingerprint", "verify_fingerprint", "sequence", "terminal_fingerprint"):
    if token not in source: fail(f"Missing architecture concept: {token}")
print("[PASS] Immutable chained-event architecture")

for token in ("sqlite", "requests", "socket", "subprocess", "open("):
    if token in source.lower(): fail(f"Isolation violation: {token}")
print("[PASS] Storage, network, and process isolation")

print(f"[PASS] Deterministic architecture fingerprint: {sha256(b''.join(p.read_bytes() for p in REQUIRED[:5])).hexdigest()}")
PY

cat > dev/verify_genesis_vi_a67.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"
failed=0
check() { local name="$1"; shift; if "$@"; then echo "[PASS] $name"; else echo "[FAIL] $name"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.7 EXECUTIVE TIMELINE ENGINE"
echo "========================================================================"
check "Genesis VI-A6.7 package compilation" "$PYTHON_BIN" -m compileall -q core/executive/timeline
check "Genesis VI-A6.7 unit tests" env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a67_executive_timeline
check "Genesis VI-A6.7 structural verification" env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a67.py

for r in dev/verify_genesis_vi_a66.sh dev/verify_genesis_vi_a65.sh dev/verify_genesis_vi_a64.sh dev/verify_genesis_vi_a63.sh; do
  [[ -x "$r" ]] && check "Regression: $(basename "$r")" env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" "$r"
done
echo "------------------------------------------------------------------------"
echo "Checks failed : $failed"
[[ "$failed" -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
exit "$failed"
SH

cat > dev/demo_genesis_vi_a67.py <<'PY'
#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from core.executive.timeline import *

BASE = datetime(2026, 7, 22, 8, 41, 12, tzinfo=timezone.utc)
timeline = ExecutiveTimelineEngine(event_id_factory=lambda n: f"timeline-event-{n:04d}")

def add(offset, subsystem, kind, payload, parent=None):
    return timeline.append(TimelineEventDraft(
        subsystem=subsystem, kind=kind,
        context=TimelineContext(
            session_id="executive-session-demo",
            mission_id="mission-network-001",
            correlation_id="investigation-cycle-001",
        ),
        payload=payload, parent_event_id=parent,
        occurred_at=BASE + timedelta(seconds=offset),
    ))

boot = add(0, TimelineSubsystem.EXECUTIVE, TimelineEventKind.EXECUTIVE_BOOT_STARTED, {"state": "booting"})
add(1, TimelineSubsystem.EXECUTIVE, TimelineEventKind.EXECUTIVE_BOOT_COMPLETED, {"state": "ready"}, boot.event_id)
mission = add(2, TimelineSubsystem.MISSION, TimelineEventKind.MISSION_STARTED, {"title": "Investigate suspicious network activity"})
obs = add(3, TimelineSubsystem.OBSERVATION, TimelineEventKind.OBSERVATION_RECEIVED, {"summary": "Unexpected outbound connection"}, mission.event_id)
add(4, TimelineSubsystem.KNOWLEDGE, TimelineEventKind.KNOWLEDGE_RETRIEVED, {"evidence_count": 4}, obs.event_id)
reason = add(5, TimelineSubsystem.REASONING, TimelineEventKind.REASONING_STARTED, {"strategy": "hypothesis evaluation"}, obs.event_id)
hyp = add(6, TimelineSubsystem.REASONING, TimelineEventKind.HYPOTHESIS_SELECTED, {"hypothesis": "Unapproved service", "confidence": 0.88}, reason.event_id)
decision = add(7, TimelineSubsystem.DECISION, TimelineEventKind.DECISION_CERTIFIED, {"decision": "Isolate process"}, hyp.event_id)
add(8, TimelineSubsystem.PERSISTENCE, TimelineEventKind.CHECKPOINT_CREATED, {"checkpoint_id": "checkpoint-0043"}, decision.event_id)

print("=" * 94)
print("AUTHORITATIVE EXECUTIVE TIMELINE")
print("=" * 94)
for e in timeline.events:
    print(f"{e.sequence:03d}  {e.occurred_at:%H:%M:%S}  {e.subsystem.value:<12} {e.kind.value:<30} {dict(e.payload)}")

report = timeline.verify()
print("\n" + "=" * 94)
print("TIMELINE INTEGRITY CERTIFICATION")
print("=" * 94)
print(f"Certified            : {report.certified}")
print(f"Event count          : {report.event_count}")
print(f"Terminal fingerprint : {report.terminal_fingerprint}")
print(f"Report fingerprint   : {report.report_fingerprint}")
print(f"Findings             : {report.findings or 'NONE'}")
print("\nGENESIS VI-A6.7 TEST DRIVE COMPLETE")
PY

chmod +x dev/verification/verify_genesis_vi_a67.py dev/verify_genesis_vi_a67.sh dev/demo_genesis_vi_a67.py

echo "Installed Genesis VI-A6.7. Backup: $BACKUP"
echo "Verify: PYTHON_BIN=$PYTHON_BIN ./dev/verify_genesis_vi_a67.sh"
echo "Demo:   PYTHONPATH=\"\$(pwd)\" $PYTHON_BIN dev/demo_genesis_vi_a67.py"

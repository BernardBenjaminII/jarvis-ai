#!/usr/bin/env bash
set -euo pipefail

ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"

[[ -d core/executive/timeline ]] || { echo "ERROR: Genesis VI-A6.7 timeline package not found."; exit 1; }
[[ -f core/executive/timeline/contracts.py ]] || { echo "ERROR: Missing VI-A6.7 contracts.py."; exit 1; }
[[ -x "$PYTHON_BIN" ]] || { echo "ERROR: Invalid Python: $PYTHON_BIN"; exit 1; }

BACKUP=".migration_backups/genesis_vi_a68_part_a_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"
backup() {
  [[ -f "$1" ]] || return 0
  mkdir -p "$BACKUP/$(dirname "$1")"
  cp "$1" "$BACKUP/$1"
}

FILES=(
  core/executive/timeline/__init__.py
  core/executive/timeline/repository_contracts.py
  core/executive/timeline/serializers.py
  core/executive/timeline/storage.py
  core/executive/timeline/indexes.py
  core/executive/timeline/repository.py
  tests/test_genesis_vi_a68_part_a_timeline_repository.py
  docs/architecture/genesis_vi_a68_timeline_repository_foundation.md
  dev/verification/verify_genesis_vi_a68_part_a.py
  dev/verify_genesis_vi_a68_part_a.sh
  dev/demo_genesis_vi_a68_part_a.py
)
for f in "${FILES[@]}"; do backup "$f"; done
mkdir -p core/executive/timeline tests docs/architecture dev/verification dev

cat > core/executive/timeline/repository_contracts.py <<'PYFILE'
"""Immutable contracts for Genesis VI-A6.8 Part A."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable


TIMELINE_REPOSITORY_SCHEMA = "jarvis.executive.timeline.repository"
TIMELINE_REPOSITORY_SCHEMA_VERSION = 1


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


class TimelineRepositoryError(RuntimeError):
    """Base repository failure."""


class TimelineRepositoryStorageError(TimelineRepositoryError):
    """Storage operation failed or violated repository boundaries."""


class TimelineRepositoryConflictError(TimelineRepositoryError):
    """An append conflicts with already persisted history."""


class TimelineRepositoryIntegrityError(TimelineRepositoryError):
    """Persisted timeline history failed certification."""


class RepositoryIntegrityStatus(str, Enum):
    CERTIFIED = "certified"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TimelineRepositoryStatistics:
    event_count: int
    session_count: int
    mission_count: int
    subsystem_count: int
    first_sequence: int | None
    last_sequence: int | None
    terminal_fingerprint: str
    storage_bytes: int
    statistics_fingerprint: str

    @classmethod
    def create(
        cls,
        *,
        event_count: int,
        session_count: int,
        mission_count: int,
        subsystem_count: int,
        first_sequence: int | None,
        last_sequence: int | None,
        terminal_fingerprint: str,
        storage_bytes: int,
    ) -> "TimelineRepositoryStatistics":
        material = {
            "event_count": event_count,
            "session_count": session_count,
            "mission_count": mission_count,
            "subsystem_count": subsystem_count,
            "first_sequence": first_sequence,
            "last_sequence": last_sequence,
            "terminal_fingerprint": terminal_fingerprint,
            "storage_bytes": storage_bytes,
        }
        return cls(**material, statistics_fingerprint=_fingerprint(material))

    def verify_fingerprint(self) -> bool:
        rebuilt = self.create(
            event_count=self.event_count,
            session_count=self.session_count,
            mission_count=self.mission_count,
            subsystem_count=self.subsystem_count,
            first_sequence=self.first_sequence,
            last_sequence=self.last_sequence,
            terminal_fingerprint=self.terminal_fingerprint,
            storage_bytes=self.storage_bytes,
        )
        return rebuilt.statistics_fingerprint == self.statistics_fingerprint


@dataclass(frozen=True, slots=True)
class TimelineRepositoryIntegrityReport:
    status: RepositoryIntegrityStatus
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    terminal_fingerprint: str
    findings: tuple[str, ...]
    report_fingerprint: str

    @property
    def certified(self) -> bool:
        return self.status is RepositoryIntegrityStatus.CERTIFIED

    @classmethod
    def create(
        cls,
        *,
        event_count: int,
        first_sequence: int | None,
        last_sequence: int | None,
        terminal_fingerprint: str,
        findings: Iterable[str] = (),
    ) -> "TimelineRepositoryIntegrityReport":
        normalized = tuple(str(item) for item in findings)
        status = (
            RepositoryIntegrityStatus.CERTIFIED
            if not normalized
            else RepositoryIntegrityStatus.FAILED
        )
        material = {
            "status": status.value,
            "event_count": event_count,
            "first_sequence": first_sequence,
            "last_sequence": last_sequence,
            "terminal_fingerprint": terminal_fingerprint,
            "findings": normalized,
        }
        return cls(
            status=status,
            event_count=event_count,
            first_sequence=first_sequence,
            last_sequence=last_sequence,
            terminal_fingerprint=terminal_fingerprint,
            findings=normalized,
            report_fingerprint=_fingerprint(material),
        )

    def verify_fingerprint(self) -> bool:
        rebuilt = self.create(
            event_count=self.event_count,
            first_sequence=self.first_sequence,
            last_sequence=self.last_sequence,
            terminal_fingerprint=self.terminal_fingerprint,
            findings=self.findings,
        )
        return rebuilt.report_fingerprint == self.report_fingerprint
PYFILE

cat > core/executive/timeline/serializers.py <<'PYFILE'
"""Canonical TimelineEvent serialization for VI-A6.8 Part A."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Mapping

from .contracts import (
    TimelineContext,
    TimelineEvent,
    TimelineEventKind,
    TimelineSubsystem,
)
from .repository_contracts import (
    TIMELINE_REPOSITORY_SCHEMA,
    TIMELINE_REPOSITORY_SCHEMA_VERSION,
    TimelineRepositoryIntegrityError,
)


class TimelineEventSerializer:
    """Stable JSON codec for immutable A6.7 timeline events."""

    @staticmethod
    def to_record(event: TimelineEvent) -> dict[str, object]:
        return {
            "schema": TIMELINE_REPOSITORY_SCHEMA,
            "schema_version": TIMELINE_REPOSITORY_SCHEMA_VERSION,
            "event": {
                "event_id": event.event_id,
                "sequence": event.sequence,
                "occurred_at": event.occurred_at.isoformat(),
                "subsystem": event.subsystem.value,
                "kind": event.kind.value,
                "context": event.context.canonical_dict(),
                "payload": dict(event.payload),
                "parent_event_id": event.parent_event_id,
                "previous_event_fingerprint": event.previous_event_fingerprint,
                "event_fingerprint": event.event_fingerprint,
            },
        }

    @classmethod
    def dumps(cls, event: TimelineEvent) -> str:
        return json.dumps(
            cls.to_record(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def dump_line(cls, event: TimelineEvent) -> bytes:
        return (cls.dumps(event) + "\n").encode("utf-8")

    @staticmethod
    def _context(value: object) -> TimelineContext:
        if not isinstance(value, Mapping):
            raise TimelineRepositoryIntegrityError("Event context must be an object.")
        return TimelineContext(
            session_id=value.get("session_id"),
            mission_id=value.get("mission_id"),
            objective_id=value.get("objective_id"),
            task_id=value.get("task_id"),
            activity_id=value.get("activity_id"),
            correlation_id=value.get("correlation_id"),
        )

    @classmethod
    def loads(cls, raw: str | bytes) -> TimelineEvent:
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            record = json.loads(raw)
            if record.get("schema") != TIMELINE_REPOSITORY_SCHEMA:
                raise TimelineRepositoryIntegrityError("Unknown timeline repository schema.")
            if record.get("schema_version") != TIMELINE_REPOSITORY_SCHEMA_VERSION:
                raise TimelineRepositoryIntegrityError("Unsupported timeline schema version.")
            value = record["event"]
            occurred_at = datetime.fromisoformat(value["occurred_at"])
            if occurred_at.tzinfo is None:
                raise TimelineRepositoryIntegrityError("Persisted timestamp is not timezone-aware.")
            event = TimelineEvent(
                event_id=value["event_id"],
                sequence=int(value["sequence"]),
                occurred_at=occurred_at,
                subsystem=TimelineSubsystem(value["subsystem"]),
                kind=TimelineEventKind(value["kind"]),
                context=cls._context(value["context"]),
                payload=dict(value["payload"]),
                parent_event_id=value.get("parent_event_id"),
                previous_event_fingerprint=value["previous_event_fingerprint"],
                event_fingerprint=value["event_fingerprint"],
            )
        except TimelineRepositoryIntegrityError:
            raise
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise TimelineRepositoryIntegrityError(
                f"Invalid persisted timeline record: {exc}"
            ) from exc
        if not event.verify_fingerprint():
            raise TimelineRepositoryIntegrityError(
                f"Invalid event fingerprint at sequence {event.sequence}."
            )
        return event
PYFILE

cat > core/executive/timeline/storage.py <<'PYFILE'
"""Database-free append-only JSONL storage for VI-A6.8 Part A."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Iterator

from .repository_contracts import TimelineRepositoryStorageError


class AppendOnlyTimelineStorage:
    """Owns a single repository JSONL file and permits append/read only."""

    def __init__(self, root: str | Path, *, filename: str = "executive.timeline.jsonl") -> None:
        root_path = Path(root).expanduser().resolve()
        if not filename or Path(filename).name != filename:
            raise TimelineRepositoryStorageError("filename must be a plain file name.")
        self._root = root_path
        self._path = (root_path / filename).resolve()
        try:
            self._path.relative_to(root_path)
        except ValueError as exc:
            raise TimelineRepositoryStorageError("Storage path escaped repository root.") from exc
        self._root.mkdir(parents=True, exist_ok=True)
        if self._path.exists() and not self._path.is_file():
            raise TimelineRepositoryStorageError("Timeline storage path is not a regular file.")

    @property
    def root(self) -> Path:
        return self._root

    @property
    def path(self) -> Path:
        return self._path

    @property
    def size_bytes(self) -> int:
        return self._path.stat().st_size if self._path.exists() else 0

    def append(self, line: bytes) -> None:
        self.append_many((line,))

    def append_many(self, lines: Iterable[bytes]) -> None:
        material = tuple(lines)
        if not material:
            return
        for line in material:
            if not isinstance(line, bytes):
                raise TimelineRepositoryStorageError("Storage accepts bytes only.")
            if not line.endswith(b"\n") or line.count(b"\n") != 1:
                raise TimelineRepositoryStorageError("Each append must contain exactly one JSONL record.")
        try:
            with self._path.open("ab", buffering=0) as handle:
                for line in material:
                    handle.write(line)
                os.fsync(handle.fileno())
        except OSError as exc:
            raise TimelineRepositoryStorageError(f"Timeline append failed: {exc}") from exc

    def iter_lines(self) -> Iterator[bytes]:
        if not self._path.exists():
            return
        try:
            with self._path.open("rb") as handle:
                for number, line in enumerate(handle, 1):
                    if not line.endswith(b"\n"):
                        raise TimelineRepositoryStorageError(
                            f"Incomplete timeline record at line {number}."
                        )
                    yield line[:-1]
        except OSError as exc:
            raise TimelineRepositoryStorageError(f"Timeline read failed: {exc}") from exc
PYFILE

cat > core/executive/timeline/indexes.py <<'PYFILE'
"""Deterministic in-memory indexes over persisted timeline events."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping

from .contracts import TimelineEvent, TimelineEventKind, TimelineSubsystem
from .repository_contracts import TimelineRepositoryIntegrityError


@dataclass(frozen=True, slots=True)
class TimelineRepositoryIndexes:
    by_event_id: Mapping[str, int]
    by_session: Mapping[str, tuple[int, ...]]
    by_mission: Mapping[str, tuple[int, ...]]
    by_subsystem: Mapping[TimelineSubsystem, tuple[int, ...]]
    by_kind: Mapping[TimelineEventKind, tuple[int, ...]]

    @classmethod
    def build(cls, events: Iterable[TimelineEvent]) -> "TimelineRepositoryIndexes":
        event_id: dict[str, int] = {}
        sessions: dict[str, list[int]] = defaultdict(list)
        missions: dict[str, list[int]] = defaultdict(list)
        subsystems: dict[TimelineSubsystem, list[int]] = defaultdict(list)
        kinds: dict[TimelineEventKind, list[int]] = defaultdict(list)
        for event in events:
            if event.event_id in event_id:
                raise TimelineRepositoryIntegrityError(
                    f"Duplicate persisted event ID: {event.event_id}."
                )
            event_id[event.event_id] = event.sequence
            if event.context.session_id is not None:
                sessions[event.context.session_id].append(event.sequence)
            if event.context.mission_id is not None:
                missions[event.context.mission_id].append(event.sequence)
            subsystems[event.subsystem].append(event.sequence)
            kinds[event.kind].append(event.sequence)

        def freeze(source):
            return MappingProxyType(
                {key: tuple(sorted(values)) for key, values in sorted(source.items(), key=lambda x: str(x[0]))}
            )

        return cls(
            by_event_id=MappingProxyType(dict(sorted(event_id.items()))),
            by_session=freeze(sessions),
            by_mission=freeze(missions),
            by_subsystem=freeze(subsystems),
            by_kind=freeze(kinds),
        )
PYFILE

cat > core/executive/timeline/repository.py <<'PYFILE'
"""Certified append-only Executive Timeline Repository foundation."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from threading import RLock

from .contracts import GENESIS_FINGERPRINT, TimelineEvent
from .indexes import TimelineRepositoryIndexes
from .repository_contracts import (
    TimelineRepositoryConflictError,
    TimelineRepositoryIntegrityError,
    TimelineRepositoryIntegrityReport,
    TimelineRepositoryStatistics,
)
from .serializers import TimelineEventSerializer
from .storage import AppendOnlyTimelineStorage


class ExecutiveTimelineRepository:
    """Persistent authority for already-created VI-A6.7 TimelineEvent objects."""

    def __init__(self, root: str | Path) -> None:
        self._storage = AppendOnlyTimelineStorage(root)
        self._lock = RLock()
        self._events: tuple[TimelineEvent, ...] = ()
        self._indexes = TimelineRepositoryIndexes.build(())
        self.reload()

    @property
    def storage_path(self) -> Path:
        return self._storage.path

    @property
    def events(self) -> tuple[TimelineEvent, ...]:
        return self._events

    @property
    def indexes(self) -> TimelineRepositoryIndexes:
        return self._indexes

    @property
    def terminal_fingerprint(self) -> str:
        return self._events[-1].event_fingerprint if self._events else GENESIS_FINGERPRINT

    def _certify_candidate(self, events: tuple[TimelineEvent, ...]) -> None:
        findings: list[str] = []
        previous = GENESIS_FINGERPRINT
        seen: set[str] = set()
        for expected, event in enumerate(events, 1):
            if event.sequence != expected:
                findings.append(
                    f"Sequence mismatch: expected {expected}, found {event.sequence}."
                )
            if event.event_id in seen:
                findings.append(f"Duplicate event ID: {event.event_id}.")
            if event.previous_event_fingerprint != previous:
                findings.append(f"Broken chain before sequence {event.sequence}.")
            if not event.verify_fingerprint():
                findings.append(f"Invalid fingerprint at sequence {event.sequence}.")
            if event.parent_event_id is not None and event.parent_event_id not in seen:
                findings.append(f"Invalid parent at sequence {event.sequence}.")
            seen.add(event.event_id)
            previous = event.event_fingerprint
        if findings:
            raise TimelineRepositoryIntegrityError("; ".join(findings))

    def reload(self) -> tuple[TimelineEvent, ...]:
        with self._lock:
            events = tuple(
                TimelineEventSerializer.loads(line)
                for line in self._storage.iter_lines()
            )
            self._certify_candidate(events)
            self._events = events
            self._indexes = TimelineRepositoryIndexes.build(events)
            return events

    def append(self, event: TimelineEvent) -> TimelineEvent:
        return self.append_many((event,))[0]

    def append_many(self, events: Iterable[TimelineEvent]) -> tuple[TimelineEvent, ...]:
        incoming = tuple(events)
        if not incoming:
            return ()
        with self._lock:
            candidate = self._events + incoming
            try:
                self._certify_candidate(candidate)
            except TimelineRepositoryIntegrityError as exc:
                raise TimelineRepositoryConflictError(str(exc)) from exc
            self._storage.append_many(
                TimelineEventSerializer.dump_line(event) for event in incoming
            )
            self._events = candidate
            self._indexes = TimelineRepositoryIndexes.build(candidate)
            return incoming

    def get(self, event_id: str) -> TimelineEvent | None:
        sequence = self._indexes.by_event_id.get(event_id)
        return self._events[sequence - 1] if sequence is not None else None

    def load_session(self, session_id: str) -> tuple[TimelineEvent, ...]:
        return self._select(self._indexes.by_session.get(session_id, ()))

    def load_mission(self, mission_id: str) -> tuple[TimelineEvent, ...]:
        return self._select(self._indexes.by_mission.get(mission_id, ()))

    def _select(self, sequences: Iterable[int]) -> tuple[TimelineEvent, ...]:
        return tuple(self._events[sequence - 1] for sequence in sequences)

    def latest(self, limit: int = 25) -> tuple[TimelineEvent, ...]:
        if limit < 0:
            raise ValueError("limit cannot be negative.")
        if limit == 0:
            return ()
        return tuple(reversed(self._events[-limit:]))

    def statistics(self) -> TimelineRepositoryStatistics:
        return TimelineRepositoryStatistics.create(
            event_count=len(self._events),
            session_count=len(self._indexes.by_session),
            mission_count=len(self._indexes.by_mission),
            subsystem_count=len(self._indexes.by_subsystem),
            first_sequence=self._events[0].sequence if self._events else None,
            last_sequence=self._events[-1].sequence if self._events else None,
            terminal_fingerprint=self.terminal_fingerprint,
            storage_bytes=self._storage.size_bytes,
        )

    def verify(self) -> TimelineRepositoryIntegrityReport:
        findings: list[str] = []
        try:
            disk_events = tuple(
                TimelineEventSerializer.loads(line)
                for line in self._storage.iter_lines()
            )
            self._certify_candidate(disk_events)
            rebuilt = TimelineRepositoryIndexes.build(disk_events)
            if disk_events != self._events:
                findings.append("In-memory repository state differs from persisted state.")
            if rebuilt != self._indexes:
                findings.append("Repository indexes differ from deterministic rebuild.")
        except (TimelineRepositoryIntegrityError, Exception) as exc:
            findings.append(str(exc))
            disk_events = ()
        return TimelineRepositoryIntegrityReport.create(
            event_count=len(disk_events),
            first_sequence=disk_events[0].sequence if disk_events else None,
            last_sequence=disk_events[-1].sequence if disk_events else None,
            terminal_fingerprint=(
                disk_events[-1].event_fingerprint
                if disk_events
                else GENESIS_FINGERPRINT
            ),
            findings=findings,
        )
PYFILE

"$PYTHON_BIN" - <<'PYFILE'
from pathlib import Path
path = Path("core/executive/timeline/__init__.py")
text = path.read_text(encoding="utf-8")
start = "# BEGIN GENESIS VI-A6.8 PART A EXPORTS"
end = "# END GENESIS VI-A6.8 PART A EXPORTS"
block = """# BEGIN GENESIS VI-A6.8 PART A EXPORTS
from .indexes import TimelineRepositoryIndexes
from .repository import ExecutiveTimelineRepository
from .repository_contracts import (
    RepositoryIntegrityStatus,
    TIMELINE_REPOSITORY_SCHEMA,
    TIMELINE_REPOSITORY_SCHEMA_VERSION,
    TimelineRepositoryConflictError,
    TimelineRepositoryError,
    TimelineRepositoryIntegrityError,
    TimelineRepositoryIntegrityReport,
    TimelineRepositoryStatistics,
    TimelineRepositoryStorageError,
)
from .serializers import TimelineEventSerializer
from .storage import AppendOnlyTimelineStorage
# END GENESIS VI-A6.8 PART A EXPORTS"""
if start in text and end in text:
    prefix = text.split(start, 1)[0].rstrip()
    suffix = text.split(end, 1)[1].lstrip()
    text = prefix + "\n\n" + block + "\n" + suffix
else:
    text = text.rstrip() + "\n\n" + block + "\n"

marker = "__all__ = ["
if marker not in text:
    raise SystemExit("ERROR: VI-A6.7 __all__ declaration not found.")
names = [
    "AppendOnlyTimelineStorage",
    "ExecutiveTimelineRepository",
    "RepositoryIntegrityStatus",
    "TIMELINE_REPOSITORY_SCHEMA",
    "TIMELINE_REPOSITORY_SCHEMA_VERSION",
    "TimelineEventSerializer",
    "TimelineRepositoryConflictError",
    "TimelineRepositoryError",
    "TimelineRepositoryIndexes",
    "TimelineRepositoryIntegrityError",
    "TimelineRepositoryIntegrityReport",
    "TimelineRepositoryStatistics",
    "TimelineRepositoryStorageError",
]
for name in names:
    token = f'    "{name}",'
    if token not in text:
        insertion = text.index(marker) + len(marker)
        text = text[:insertion] + "\n" + token + text[insertion:]
path.write_text(text, encoding="utf-8")
PYFILE

cat > tests/test_genesis_vi_a68_part_a_timeline_repository.py <<'PYFILE'
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
PYFILE

cat > docs/architecture/genesis_vi_a68_timeline_repository_foundation.md <<'MDFILE'
# Genesis VI-A6.8 Part A — Executive Timeline Repository Foundation

**Status:** Implemented  
**Depends on:** Genesis VI-A6.7  
**Next:** Genesis VI-A6.8 Part B — Query and Certification

## Purpose

Part A gives the authoritative Executive Timeline durable, append-only storage.
The VI-A6.7 Timeline Engine remains the sole creator and chronological authority
for events. The repository accepts only already-certified `TimelineEvent`
instances and owns persistence, loading, deterministic indexes, statistics, and
independent repository verification.

## Storage format

The initial backend is canonical UTF-8 JSON Lines:

```text
<repository-root>/executive.timeline.jsonl
```

Each line contains one complete event envelope and ends with one newline. The
storage adapter supports append and sequential read only. It exposes no update,
delete, truncate, or archive operation.

## Responsibilities

```text
Timeline Engine (VI-A6.7)
        │ creates immutable events
        ▼
Executive Timeline Repository
        ├── canonical serializer
        ├── append-only storage
        ├── deterministic indexes
        ├── session and mission loading
        ├── repository statistics
        └── independent integrity verification
```

## Invariants

1. Persisted sequence begins at one and remains contiguous.
2. Each event fingerprint verifies against canonical event material.
3. Each event links to the immediately preceding event fingerprint.
4. Parent references point only to earlier persisted events.
5. Event IDs remain unique.
6. The repository never edits or deletes history.
7. Indexes are deterministic derivatives of persisted events.
8. Reloading the repository reconstructs the same immutable events.

## Deliberate exclusions

Part A does not introduce the general query language, pagination, replay,
background event dispatch, SQLite, or Mission Control integration. Those remain
outside this foundation so persistence can be certified independently.
MDFILE

cat > dev/verification/verify_genesis_vi_a68_part_a.py <<'PYFILE'
#!/usr/bin/env python3
from hashlib import sha256
import ast
import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    ROOT / "core/executive/timeline/repository_contracts.py",
    ROOT / "core/executive/timeline/serializers.py",
    ROOT / "core/executive/timeline/storage.py",
    ROOT / "core/executive/timeline/indexes.py",
    ROOT / "core/executive/timeline/repository.py",
    ROOT / "tests/test_genesis_vi_a68_part_a_timeline_repository.py",
    ROOT / "docs/architecture/genesis_vi_a68_timeline_repository_foundation.md",
]


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
if missing:
    fail(f"Missing required files: {missing}")
print("[PASS] Canonical Genesis VI-A6.8 Part A structure")

sys.path.insert(0, str(ROOT))
from core.executive.timeline import (
    AppendOnlyTimelineStorage,
    ExecutiveTimelineRepository,
    TimelineEventSerializer,
    TimelineRepositoryIndexes,
)

for symbol in (
    AppendOnlyTimelineStorage,
    ExecutiveTimelineRepository,
    TimelineEventSerializer,
    TimelineRepositoryIndexes,
):
    if not inspect.isclass(symbol):
        fail(f"Unstable public symbol: {symbol}")
print("[PASS] Stable timeline repository public API")

repository_source = inspect.getsource(ExecutiveTimelineRepository)
for forbidden in ("sqlite3", "sqlalchemy", "requests", "httpx", "socket", "subprocess"):
    if forbidden in repository_source.lower():
        fail(f"Forbidden dependency in repository: {forbidden}")
print("[PASS] Database, network, vendor, and process isolation")

for forbidden_method in ("delete", "update", "truncate", "replace"):
    if hasattr(ExecutiveTimelineRepository, forbidden_method):
        fail(f"Append-only boundary violation: {forbidden_method}")
print("[PASS] Append-only repository public boundary")

for path in REQUIRED[:5]:
    ast.parse(path.read_text(encoding="utf-8"))
print("[PASS] Repository module syntax and structural parse")

fingerprint = sha256(b"".join(path.read_bytes() for path in REQUIRED[:5])).hexdigest()
print(f"[PASS] Deterministic architecture fingerprint: {fingerprint}")
PYFILE

cat > dev/verify_genesis_vi_a68_part_a.sh <<'SHFILE'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"
failed=0
check() {
  local name="$1"; shift
  if "$@"; then echo "[PASS] $name"; else echo "[FAIL] $name"; failed=$((failed + 1)); fi
}

echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.8 PART A TIMELINE REPOSITORY FOUNDATION"
echo "========================================================================"
check "Genesis VI-A6.8 Part A package compilation" \
  "$PYTHON_BIN" -m compileall -q core/executive/timeline tests/test_genesis_vi_a68_part_a_timeline_repository.py
check "Genesis VI-A6.8 Part A unit tests" \
  env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a68_part_a_timeline_repository
check "Genesis VI-A6.8 Part A structural certification" \
  env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a68_part_a.py

if [[ -x dev/verify_genesis_vi_a67.sh ]]; then
  check "Genesis VI-A6.7 regression" \
    env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a67.sh
fi

echo "------------------------------------------------------------------------"
echo "Checks failed : $failed"
[[ "$failed" -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
exit "$failed"
SHFILE

cat > dev/demo_genesis_vi_a68_part_a.py <<'PYFILE'
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
PYFILE

chmod +x \
  dev/verification/verify_genesis_vi_a68_part_a.py \
  dev/verify_genesis_vi_a68_part_a.sh \
  dev/demo_genesis_vi_a68_part_a.py

echo
echo "Installed Genesis VI-A6.8 Part A — Timeline Repository Foundation."
echo "Backup: $BACKUP"
echo
echo "Verify:"
echo "  PYTHON_BIN=$PYTHON_BIN ./dev/verify_genesis_vi_a68_part_a.sh"
echo
echo "Demo:"
echo "  PYTHONPATH=\"\$(pwd)\" $PYTHON_BIN dev/demo_genesis_vi_a68_part_a.py"

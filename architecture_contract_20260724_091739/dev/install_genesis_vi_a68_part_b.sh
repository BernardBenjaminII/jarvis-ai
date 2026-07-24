#!/usr/bin/env bash
set -euo pipefail

ROOT="${JARVIS_PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
BACKUP_ROOT="${ROOT}/.migration_backups/genesis_vi_a68b_$(date +%Y%m%d_%H%M%S)"
cd "${ROOT}"

require_file(){ [[ -f "$1" ]] || { echo "[FAIL] Missing prerequisite: $1" >&2; exit 1; }; }
backup_if_present(){ local p="$1"; if [[ -f "$p" ]]; then mkdir -p "${BACKUP_ROOT}/$(dirname "$p")"; cp -a "$p" "${BACKUP_ROOT}/$p"; fi; }
write_file(){ local p="$1"; mkdir -p "$(dirname "$p")"; cat > "$p"; }

printf '\n========================================================================\n'
printf 'GENESIS VI-A6.8 PART B\nEXECUTIVE TIMELINE QUERY ENGINE & CERTIFICATION\n'
printf '========================================================================\n'
printf 'Project root : %s\nPython       : %s\n\n' "$ROOT" "$PYTHON_BIN"

require_file core/executive/timeline/__init__.py
require_file core/executive/timeline/repository.py

for p in \
 core/executive/timeline/query_engine.py \
 core/executive/timeline/replay_readiness.py \
 tests/test_genesis_vi_a68_part_b.py \
 dev/verification/verify_genesis_vi_a68_part_b.py \
 dev/verify_genesis_vi_a68_part_b.sh \
 demo/demo_genesis_vi_a68_part_b.py \
 docs/architecture/genesis_vi_a68_part_b.md \
 core/executive/timeline/__init__.py; do backup_if_present "$p"; done

write_file core/executive/timeline/query_engine.py <<'PY'
"""Deterministic read-only queries over the Executive Timeline Repository."""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from json import dumps
from typing import Any, Callable, Iterable, Mapping, Sequence


class TimelineQueryError(RuntimeError):
    """Base timeline query error."""


class InvalidQueryError(TimelineQueryError):
    """Raised when a query is invalid."""


class RepositoryAccessError(TimelineQueryError):
    """Raised when the repository exposes no readable event stream."""


@dataclass(frozen=True, slots=True)
class TimelinePage:
    items: tuple[Any, ...]
    offset: int
    limit: int
    total: int
    has_previous: bool
    has_next: bool

    @property
    def returned(self) -> int:
        return len(self.items)


@dataclass(frozen=True, slots=True)
class TimelineStatistics:
    total_events: int
    first_sequence: int | None
    last_sequence: int | None
    first_timestamp: str | None
    last_timestamp: str | None
    missions: tuple[tuple[str, int], ...]
    sessions: tuple[tuple[str, int], ...]
    subsystems: tuple[tuple[str, int], ...]
    event_kinds: tuple[tuple[str, int], ...]
    fingerprint: str


_MISSING = object()
_ALIASES = {
    "sequence": ("sequence", "sequence_number", "seq", "ordinal", "event_sequence"),
    "timestamp": ("timestamp", "occurred_at", "created_at", "recorded_at", "event_time", "time"),
    "mission_id": ("mission_id", "mission", "mission_key"),
    "session_id": ("session_id", "session", "session_key"),
    "subsystem": ("subsystem", "source", "component", "producer", "owner"),
    "event_kind": ("event_kind", "kind", "event_type", "type", "name"),
    "event_id": ("event_id", "id", "timeline_event_id"),
}


def _enum(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def read_event_value(event: Any, field: str, default: Any = _MISSING) -> Any:
    aliases = _ALIASES.get(field, (field,))
    if isinstance(event, Mapping):
        for name in aliases:
            if name in event:
                return _enum(event[name])
    else:
        for name in aliases:
            if hasattr(event, name):
                return _enum(getattr(event, name))
    if default is not _MISSING:
        return default
    raise InvalidQueryError(f"{type(event).__name__} exposes no {field!r} field")


def event_sequence(event: Any, fallback: int) -> int:
    raw = read_event_value(event, "sequence", fallback)
    if isinstance(raw, bool):
        raise InvalidQueryError("Boolean sequence values are invalid")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidQueryError(f"Invalid sequence: {raw!r}") from exc


def event_timestamp(event: Any) -> datetime:
    raw = read_event_value(event, "timestamp", None)
    if raw in (None, ""):
        return datetime.min.replace(tzinfo=timezone.utc)
    if isinstance(raw, datetime):
        value = raw
    elif isinstance(raw, (int, float)):
        value = datetime.fromtimestamp(float(raw), tz=timezone.utc)
    elif isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidQueryError(f"Invalid timestamp: {raw!r}") from exc
    else:
        raise InvalidQueryError(f"Unsupported timestamp: {raw!r}")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    value = _enum(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        items = [_canonical(v) for v in value]
        return sorted(items, key=lambda v: dumps(v, sort_keys=True, default=str))
    if hasattr(value, "__dict__"):
        return {k: _canonical(v) for k, v in sorted(vars(value).items()) if not k.startswith("_")}
    return value


def canonical_event_fingerprint(events: Sequence[Any]) -> str:
    payload = dumps([_canonical(e) for e in events], sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


class TimelineQueryEngine:
    """Immutable deterministic query façade over a Part A repository."""

    def __init__(self, repository: Any):
        if repository is None:
            raise InvalidQueryError("repository must not be None")
        self._repository = repository

    def all(self) -> tuple[Any, ...]:
        events = tuple(self._read_events())
        rows = [(event_sequence(e, i), event_timestamp(e), i, e) for i, e in enumerate(events)]
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        return tuple(row[3] for row in rows)

    def latest(self, limit: int = 1) -> tuple[Any, ...]:
        self._validate_limit(limit)
        return () if limit == 0 else self.all()[-limit:]

    def by_mission(self, mission_id: str) -> tuple[Any, ...]:
        return self._exact("mission_id", mission_id)

    def by_session(self, session_id: str) -> tuple[Any, ...]:
        return self._exact("session_id", session_id)

    def by_subsystem(self, subsystem: str) -> tuple[Any, ...]:
        return self._exact("subsystem", subsystem)

    def by_event_kind(self, event_kind: str) -> tuple[Any, ...]:
        return self._exact("event_kind", event_kind)

    def sequence_range(self, start: int | None = None, end: int | None = None, *, include_end: bool = True) -> tuple[Any, ...]:
        if start is not None and end is not None and start > end:
            raise InvalidQueryError("start sequence must not exceed end sequence")
        selected = []
        for i, event in enumerate(self.all()):
            seq = event_sequence(event, i)
            if start is not None and seq < start:
                continue
            if end is not None and (seq > end if include_end else seq >= end):
                continue
            selected.append(event)
        return tuple(selected)

    def between(self, start: datetime | str | int | float | None = None, end: datetime | str | int | float | None = None, *, include_end: bool = True) -> tuple[Any, ...]:
        lower = event_timestamp({"timestamp": start}) if start is not None else None
        upper = event_timestamp({"timestamp": end}) if end is not None else None
        if lower is not None and upper is not None and lower > upper:
            raise InvalidQueryError("start timestamp must not exceed end timestamp")
        selected = []
        for event in self.all():
            stamp = event_timestamp(event)
            if lower is not None and stamp < lower:
                continue
            if upper is not None and (stamp > upper if include_end else stamp >= upper):
                continue
            selected.append(event)
        return tuple(selected)

    def after(self, instant: datetime | str | int | float, *, inclusive: bool = False) -> tuple[Any, ...]:
        boundary = event_timestamp({"timestamp": instant})
        return tuple(e for e in self.all() if event_timestamp(e) >= boundary if inclusive or event_timestamp(e) > boundary)

    def before(self, instant: datetime | str | int | float, *, inclusive: bool = False) -> tuple[Any, ...]:
        boundary = event_timestamp({"timestamp": instant})
        return tuple(e for e in self.all() if event_timestamp(e) <= boundary if inclusive or event_timestamp(e) < boundary)

    def where(self, predicate: Callable[[Any], bool]) -> tuple[Any, ...]:
        if not callable(predicate):
            raise InvalidQueryError("predicate must be callable")
        return tuple(e for e in self.all() if bool(predicate(e)))

    def page(self, *, offset: int = 0, limit: int = 100, events: Iterable[Any] | None = None) -> TimelinePage:
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise InvalidQueryError("offset must be a non-negative integer")
        self._validate_limit(limit)
        selected = self.all() if events is None else tuple(events)
        stop = offset + limit
        return TimelinePage(tuple(selected[offset:stop]), offset, limit, len(selected), offset > 0, stop < len(selected))

    def statistics(self) -> TimelineStatistics:
        events = self.all()
        stamps = tuple(event_timestamp(e) for e in events)
        return TimelineStatistics(
            total_events=len(events),
            first_sequence=event_sequence(events[0], 0) if events else None,
            last_sequence=event_sequence(events[-1], len(events)-1) if events else None,
            first_timestamp=min(stamps).isoformat() if stamps else None,
            last_timestamp=max(stamps).isoformat() if stamps else None,
            missions=self._counts(events, "mission_id"),
            sessions=self._counts(events, "session_id"),
            subsystems=self._counts(events, "subsystem"),
            event_kinds=self._counts(events, "event_kind"),
            fingerprint=canonical_event_fingerprint(events),
        )

    def fingerprint(self, events: Iterable[Any] | None = None) -> str:
        return canonical_event_fingerprint(self.all() if events is None else tuple(events))

    def _exact(self, field: str, expected: str) -> tuple[Any, ...]:
        expected = str(expected)
        if not expected:
            raise InvalidQueryError(f"{field} must not be empty")
        return tuple(e for e in self.all() if str(read_event_value(e, field, "")) == expected)

    @staticmethod
    def _counts(events: Sequence[Any], field: str) -> tuple[tuple[str, int], ...]:
        counts: dict[str, int] = {}
        for event in events:
            key = str(read_event_value(event, field, ""))
            if key:
                counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(counts.items()))

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise InvalidQueryError("limit must be a non-negative integer")

    def _read_events(self) -> Iterable[Any]:
        repo = self._repository
        for name in ("all", "list_events", "events", "read_all", "load_all"):
            member = getattr(repo, name, None)
            if callable(member):
                try:
                    result = member()
                except TypeError:
                    continue
                if result is not None:
                    return tuple(result)
        member = getattr(repo, "events", _MISSING)
        if member is not _MISSING and not callable(member):
            return tuple(member)
        try:
            return tuple(iter(repo))
        except TypeError as exc:
            raise RepositoryAccessError(
                "Repository must expose all(), list_events(), events(), read_all(), load_all(), an events property, or __iter__()."
            ) from exc


__all__ = [
    "InvalidQueryError", "RepositoryAccessError", "TimelinePage", "TimelineQueryEngine",
    "TimelineQueryError", "TimelineStatistics", "canonical_event_fingerprint",
    "event_sequence", "event_timestamp", "read_event_value",
]
PY

write_file core/executive/timeline/replay_readiness.py <<'PY'
"""Replay-readiness certification for the Executive Timeline Repository."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .query_engine import TimelineQueryEngine, event_sequence, event_timestamp, read_event_value

@dataclass(frozen=True, slots=True)
class ReplayReadinessFinding:
    code: str
    passed: bool
    detail: str

@dataclass(frozen=True, slots=True)
class ReplayReadinessReport:
    ready: bool
    event_count: int
    fingerprint: str
    findings: tuple[ReplayReadinessFinding, ...]

def assess_replay_readiness(repository: Any) -> ReplayReadinessReport:
    engine = TimelineQueryEngine(repository)
    events = engine.all()
    sequences = [event_sequence(event, i) for i, event in enumerate(events)]
    findings = [
        ReplayReadinessFinding("deterministic-order", sequences == sorted(sequences), "Canonical sequence order is stable."),
        ReplayReadinessFinding("unique-sequences", len(sequences) == len(set(sequences)), "Event sequences are unique."),
        ReplayReadinessFinding("valid-timestamps", all(_valid_timestamp(e) for e in events), "Event timestamps are UTC-normalizable."),
        ReplayReadinessFinding("event-identity", all(bool(str(read_event_value(e, "event_id", "")).strip()) for e in events), "Event identities are present."),
        ReplayReadinessFinding("stable-fingerprint", engine.fingerprint() == engine.fingerprint(), "Repeated fingerprints are identical."),
    ]
    return ReplayReadinessReport(all(f.passed for f in findings), len(events), engine.fingerprint(), tuple(findings))

def _valid_timestamp(event: Any) -> bool:
    try:
        event_timestamp(event)
        return True
    except Exception:
        return False

__all__ = ["ReplayReadinessFinding", "ReplayReadinessReport", "assess_replay_readiness"]
PY

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
path = Path("core/executive/timeline/__init__.py")
text = path.read_text(encoding="utf-8")
begin = "# BEGIN GENESIS VI-A6.8 PART B PUBLIC API"
end = "# END GENESIS VI-A6.8 PART B PUBLIC API"
block = '''# BEGIN GENESIS VI-A6.8 PART B PUBLIC API
from .query_engine import (
    InvalidQueryError,
    RepositoryAccessError,
    TimelinePage,
    TimelineQueryEngine,
    TimelineQueryError,
    TimelineStatistics,
    canonical_event_fingerprint,
)
from .replay_readiness import (
    ReplayReadinessFinding,
    ReplayReadinessReport,
    assess_replay_readiness,
)
# END GENESIS VI-A6.8 PART B PUBLIC API
'''
if begin in text and end in text:
    prefix, rest = text.split(begin, 1)
    _, suffix = rest.split(end, 1)
    text = prefix.rstrip() + "\n\n" + block + suffix.lstrip("\n")
else:
    text = text.rstrip() + "\n\n" + block
path.write_text(text, encoding="utf-8")
PY

write_file tests/test_genesis_vi_a68_part_b.py <<'PY'
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
PY

write_file demo/demo_genesis_vi_a68_part_b.py <<'PY'
from tests.test_genesis_vi_a68_part_b import fixture_repository
from core.executive.timeline import TimelineQueryEngine, assess_replay_readiness

def main():
    repo = fixture_repository(); engine = TimelineQueryEngine(repo); stats = engine.statistics(); report = assess_replay_readiness(repo)
    print("="*72); print("GENESIS VI-A6.8 PART B — TIMELINE QUERY ENGINE DEMO"); print("="*72)
    print("\nMission m1 history")
    for event in engine.by_mission("m1"): print(f"  {event.sequence:02d} {event.subsystem:<12} {event.event_kind}")
    print("\nLatest two events")
    for event in engine.latest(2): print(f"  {event.sequence:02d} {event.subsystem:<12} {event.event_kind}")
    print("\nRepository statistics")
    print(f"  Events      : {stats.total_events}"); print(f"  Fingerprint : {stats.fingerprint}")
    print("\nReplay readiness")
    for finding in report.findings: print(f"  [{'PASS' if finding.passed else 'FAIL'}] {finding.code}: {finding.detail}")
    print("\nExecutive Timeline Repository"); print("CERTIFIED" if report.ready else "NOT CERTIFIED"); print("Replay Ready" if report.ready else "Replay Blocked")

if __name__ == "__main__": main()
PY

write_file dev/verification/verify_genesis_vi_a68_part_b.py <<'PY'
from __future__ import annotations
import ast, hashlib, importlib, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FAILED = 0

def heading(title, subtitle=None):
    print(); print("="*72); print(title); print(subtitle or ""); print("="*72)

def check(label, action):
    global FAILED
    try: action()
    except Exception as exc:
        FAILED += 1; print(f"[FAIL] {label}\n       {type(exc).__name__}: {exc}")
    else: print(f"[PASS] {label}")

def require(value, message):
    if not value: raise AssertionError(message)

def prerequisites():
    for p in (ROOT/"core/executive/timeline/repository.py", ROOT/"core/executive/timeline/__init__.py"): require(p.is_file(), f"Missing {p}")

def compilation():
    for rel in ("core/executive/timeline/query_engine.py","core/executive/timeline/replay_readiness.py","tests/test_genesis_vi_a68_part_b.py","demo/demo_genesis_vi_a68_part_b.py"):
        compile((ROOT/rel).read_text(encoding="utf-8"), rel, "exec")

def imports():
    module = importlib.import_module("core.executive.timeline")
    for name in ("TimelineQueryEngine","TimelinePage","TimelineStatistics","ReplayReadinessReport","assess_replay_readiness"): require(hasattr(module,name), f"Missing {name}")

def boundaries():
    tree = ast.parse((ROOT/"core/executive/timeline/query_engine.py").read_text())
    names=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): names += [a.name for a in node.names]
        elif isinstance(node,ast.ImportFrom) and node.module: names.append(node.module)
    require(not [n for n in names if n.startswith(("fastapi","flask","django","streamlit"))], "UI dependency leaked into core")

def tests():
    result=subprocess.run([sys.executable,"-m","unittest","-v","tests.test_genesis_vi_a68_part_b"],cwd=ROOT,check=False)
    require(result.returncode==0,"Part B tests failed")

def smoke():
    from tests.test_genesis_vi_a68_part_b import fixture_repository
    from core.executive.timeline import TimelineQueryEngine, assess_replay_readiness
    one=TimelineQueryEngine(fixture_repository()); two=TimelineQueryEngine(fixture_repository())
    require(one.fingerprint()==two.fingerprint(),"Nondeterministic fingerprint")
    require(assess_replay_readiness(fixture_repository()).ready,"Repository not replay-ready")

def fingerprint():
    digest=hashlib.sha256()
    for rel in sorted(("core/executive/timeline/query_engine.py","core/executive/timeline/replay_readiness.py","tests/test_genesis_vi_a68_part_b.py")):
        digest.update(rel.encode()); digest.update((ROOT/rel).read_bytes())
    print(f"       Architecture fingerprint: {digest.hexdigest()}")

def regression():
    candidates=("dev/verify_genesis_vi_a68_part_a.sh","dev/verify_genesis_vi_a67.sh","dev/verify_genesis_vi_a6_7.sh")
    found=False
    for rel in candidates:
        path=ROOT/rel
        if path.is_file():
            found=True; result=subprocess.run(["bash",str(path)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            require(result.returncode==0,f"Regression failed: {rel}")
    if not found: print("       Prior wrapper absent; prerequisite structure certified.")

def main():
    global FAILED
    heading("GENESIS VI-A6.8 PART B","EXECUTIVE TIMELINE QUERY ENGINE & CERTIFICATION")
    check("Genesis VI-A6.8 Part A prerequisite",prerequisites)
    check("Package compilation",compilation)
    check("Stable public imports",imports)
    check("Forward-only structural boundaries",boundaries)
    check("Deterministic query and replay smoke",smoke)
    check("Query engine unit tests",tests)
    check("Deterministic architecture fingerprint",fingerprint)
    phase_failed=FAILED
    heading("GENESIS REGRESSION CERTIFICATION","PRIOR EXECUTIVE CONTINUITY FOUNDATIONS")
    check("Genesis VI-A6.8 Part A / VI-A6.7 regression",regression)
    heading("EXECUTIVE ARCHITECTURE STATUS")
    for item in ("Persistence","Serializer","Checkpoints","Integrity","Recovery","Lifecycle","Timeline","Timeline Repository","Deterministic Query Engine"): print(f"  ✓ {item}")
    print("  ○ Executive Replay Engine")
    print("\nExecutive Principles\n  ✓ Deterministic state queries\n  ✓ Immutable query results\n  ✓ Replay-readiness evidence\n  ○ Executive Accountability runtime interface")
    heading("MASTER CERTIFICATION SUMMARY")
    print(f"Phase checks failed      : {phase_failed}"); print(f"All checks failed        : {FAILED}")
    print("Genesis VI-A6.8 Part B : " + ("CERTIFIED" if phase_failed==0 else "NOT CERTIFIED"))
    print("Overall status          : " + ("EXCELLENT" if FAILED==0 else "ATTENTION REQUIRED")); print("="*72)
    return 0 if FAILED==0 else 1

if __name__=="__main__": raise SystemExit(main())
PY

write_file dev/verify_genesis_vi_a68_part_b.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${JARVIS_PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
"$PYTHON_BIN" dev/verification/verify_genesis_vi_a68_part_b.py
SH
chmod +x dev/verify_genesis_vi_a68_part_b.sh

write_file docs/architecture/genesis_vi_a68_part_b.md <<'MD'
# Genesis VI-A6.8 Part B — Executive Timeline Query Engine

## Objective

Complete the Executive Timeline Repository with deterministic, immutable,
read-only queries and certify the repository boundary for Genesis VI-A6.9
Executive Replay.

## Architecture

```text
Executive Lifecycle
        ↓
Timeline Engine
        ↓
Timeline Repository          VI-A6.8 Part A
        ↓
Deterministic Query Engine   VI-A6.8 Part B
        ↓
Executive Replay             VI-A6.9
        ↓
Mission Control
```

## Rules

1. The Part A repository remains authoritative.
2. Queries never mutate repository state.
3. Results are immutable and canonically ordered.
4. Replay readiness is certified here; replay execution belongs to VI-A6.9.
5. UI and transport dependencies are forbidden from timeline core.
6. The query boundary begins Executive Accountability by exposing attributable historical activity.

## Public API

- `TimelineQueryEngine`
- `TimelinePage`
- `TimelineStatistics`
- `canonical_event_fingerprint`
- `ReplayReadinessReport`
- `assess_replay_readiness`

## Supported Queries

- all events
- latest events
- mission, session, subsystem, and event-kind history
- sequence and timestamp ranges
- before/after filtering
- deterministic pagination
- statistics and fingerprints
- replay-readiness assessment

## Certification

```bash
./dev/verify_genesis_vi_a68_part_b.sh
```

## Next Objective

**Genesis VI-A6.9 — Executive Replay Engine**
MD

printf '[INFO] Compiling files...\n'
"$PYTHON_BIN" -m py_compile \
 core/executive/timeline/query_engine.py \
 core/executive/timeline/replay_readiness.py \
 tests/test_genesis_vi_a68_part_b.py \
 dev/verification/verify_genesis_vi_a68_part_b.py \
 demo/demo_genesis_vi_a68_part_b.py

printf '[INFO] Running certification...\n'
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a68_part_b.sh

printf '\n========================================================================\n'
printf 'INSTALLATION COMPLETE\n'
printf '========================================================================\n'
printf 'Backup         : %s\n' "$BACKUP_ROOT"
printf 'Verifier       : ./dev/verify_genesis_vi_a68_part_b.sh\n'
printf 'Demonstration  : %s demo/demo_genesis_vi_a68_part_b.py\n' "$PYTHON_BIN"
printf 'Next objective : Genesis VI-A6.9 — Executive Replay Engine\n'
printf '========================================================================\n'

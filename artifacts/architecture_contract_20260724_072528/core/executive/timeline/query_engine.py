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

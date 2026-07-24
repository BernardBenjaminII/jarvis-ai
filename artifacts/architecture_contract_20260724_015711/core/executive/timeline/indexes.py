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

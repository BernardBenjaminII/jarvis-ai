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

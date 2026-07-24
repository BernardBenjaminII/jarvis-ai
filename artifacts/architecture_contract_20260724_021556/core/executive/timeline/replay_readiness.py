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

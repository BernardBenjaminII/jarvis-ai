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

"""Canonical Operations events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import uuid4

from .enums import EventKind
from .models import Provenance, SerializableSnapshot, utc_now


@dataclass(frozen=True, slots=True)
class OperationsEvent(SerializableSnapshot):
    event_id: str
    kind: EventKind
    occurred_at: datetime
    summary: str
    subject_id: str | None
    payload: Mapping[str, Any]
    provenance: Provenance

    @classmethod
    def create(
        cls,
        *,
        kind: EventKind,
        summary: str,
        subject_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        source: str = "operations",
        source_version: str = "mc1001",
        occurred_at: datetime | None = None,
        event_id: str | None = None,
    ) -> "OperationsEvent":
        timestamp = occurred_at or utc_now()
        return cls(
            event_id=event_id or str(uuid4()),
            kind=kind,
            occurred_at=timestamp,
            summary=summary,
            subject_id=subject_id,
            payload=dict(payload or {}),
            provenance=Provenance(
                source=source,
                source_version=source_version,
                captured_at=timestamp,
            ),
        )

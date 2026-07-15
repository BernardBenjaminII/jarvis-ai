"""
Immutable provenance contracts for JARVIS acquisition.

These models describe durable source identity, sightings, and admission
history. They contain no SQL and perform no filesystem or network access.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from knowledge_engine.acquisition.admission.models import (
    AdmissionDecision,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


def build_candidate_id(
    *,
    provider_id: str,
    source_uri: str,
) -> str:
    """Build a deterministic source identity."""

    normalized_provider = provider_id.strip().lower()
    normalized_uri = source_uri.strip()

    if not normalized_provider:
        raise ValueError("provider_id must not be empty")

    if not normalized_uri:
        raise ValueError("source_uri must not be empty")

    payload = (
        f"{normalized_provider}\n{normalized_uri}"
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """Current durable provenance state for one source identity."""

    candidate_id: str
    provider_id: str
    source_uri: str
    local_path: str
    filename: str
    checksum_sha256: str
    first_seen_at: str
    last_seen_at: str
    sighting_count: int
    last_action: str
    last_decision_fingerprint: str
    campaign_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("candidate_id", self.candidate_id),
            ("provider_id", self.provider_id),
            ("source_uri", self.source_uri),
            ("local_path", self.local_path),
            ("filename", self.filename),
            ("checksum_sha256", self.checksum_sha256),
            ("first_seen_at", self.first_seen_at),
            ("last_seen_at", self.last_seen_at),
            ("last_action", self.last_action),
            (
                "last_decision_fingerprint",
                self.last_decision_fingerprint,
            ),
        ):
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )

        for name, value in (
            ("candidate_id", self.candidate_id),
            ("checksum_sha256", self.checksum_sha256),
            (
                "last_decision_fingerprint",
                self.last_decision_fingerprint,
            ),
        ):
            if len(value) != 64:
                raise ValueError(
                    f"{name} must contain 64 hexadecimal characters"
                )

            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(
                    f"{name} must be hexadecimal"
                ) from exc

        if self.sighting_count < 1:
            raise ValueError(
                "sighting_count must be at least 1"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "provider_id": self.provider_id,
            "source_uri": self.source_uri,
            "local_path": self.local_path,
            "filename": self.filename,
            "checksum_sha256": self.checksum_sha256,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "sighting_count": self.sighting_count,
            "last_action": self.last_action,
            "last_decision_fingerprint": (
                self.last_decision_fingerprint
            ),
            "campaign_id": self.campaign_id,
        }


@dataclass(frozen=True, slots=True)
class AdmissionHistoryRecord:
    """One immutable historical admission observation."""

    history_id: int
    candidate_id: str
    seen_at: str
    action: str
    decision_fingerprint: str
    decision_json: str
    campaign_id: str | None = None

    def __post_init__(self) -> None:
        if self.history_id < 1:
            raise ValueError(
                "history_id must be at least 1"
            )

        for name, value in (
            ("candidate_id", self.candidate_id),
            ("seen_at", self.seen_at),
            ("action", self.action),
            (
                "decision_fingerprint",
                self.decision_fingerprint,
            ),
            ("decision_json", self.decision_json),
        ):
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )


@dataclass(frozen=True, slots=True)
class ProvenanceWriteResult:
    """Result of recording one candidate sighting."""

    record: ProvenanceRecord
    history: AdmissionHistoryRecord
    created: bool

    @property
    def candidate_id(self) -> str:
        return self.record.candidate_id

    @property
    def sighting_count(self) -> int:
        return self.record.sighting_count


def candidate_id_for_decision(
    decision: AdmissionDecision,
) -> str:
    """Build the durable identity represented by a decision."""

    candidate: SourceCandidate = decision.candidate

    return build_candidate_id(
        provider_id=candidate.provider_id,
        source_uri=candidate.source_uri,
    )


__all__ = [
    "AdmissionHistoryRecord",
    "ProvenanceRecord",
    "ProvenanceWriteResult",
    "build_candidate_id",
    "candidate_id_for_decision",
]

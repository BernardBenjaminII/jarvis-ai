"""Canonical models for Genesis IV-A2 Executive Situation Model."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from core.cognition.observation import Observation, ObservationSeverity

from .enums import SituationRelationType, SituationStatus
from .errors import InvalidSituationError, ObservationCompatibilityError


_SEVERITY_RANK = {
    ObservationSeverity.DEBUG: 0,
    ObservationSeverity.INFORMATIONAL: 1,
    ObservationSeverity.NOTICE: 2,
    ObservationSeverity.WARNING: 3,
    ObservationSeverity.ERROR: 4,
    ObservationSeverity.CRITICAL: 5,
}


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidSituationError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidSituationError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _required(value: str, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise InvalidSituationError(f"{field_name} must not be empty")
    return normalized


def _confidence(value: float) -> float:
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise InvalidSituationError(
            "confidence must be finite and between 0.0 and 1.0"
        )
    return normalized


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _label_pairs(
    labels: Mapping[str, str] | None,
) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()

    normalized: list[tuple[str, str]] = []
    for raw_key, raw_value in labels.items():
        key = str(raw_key).strip()
        value = str(raw_value).strip()
        if not key or not value:
            raise InvalidSituationError(
                "situation labels require non-empty keys and values"
            )
        normalized.append((key, value))

    return tuple(sorted(normalized))


def _require_observation(value: Observation) -> Observation:
    if not isinstance(value, Observation):
        raise ObservationCompatibilityError(
            "situation inputs must be Genesis IV-A1 Observation objects"
        )
    return value


@dataclass(frozen=True, slots=True)
class SituationRelation:
    """Explicit relation between two observations."""

    source_observation_id: str
    target_observation_id: str
    relation_type: SituationRelationType
    confidence: float = 1.0
    rationale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_observation_id",
            _required(
                self.source_observation_id,
                "source_observation_id",
            ),
        )
        object.__setattr__(
            self,
            "target_observation_id",
            _required(
                self.target_observation_id,
                "target_observation_id",
            ),
        )

        if self.source_observation_id == self.target_observation_id:
            raise InvalidSituationError(
                "a situation relation cannot target the same observation"
            )

        if not isinstance(self.relation_type, SituationRelationType):
            object.__setattr__(
                self,
                "relation_type",
                SituationRelationType(str(self.relation_type)),
            )

        object.__setattr__(
            self,
            "confidence",
            _confidence(self.confidence),
        )

        if self.rationale is not None:
            rationale = str(self.rationale).strip()
            object.__setattr__(self, "rationale", rationale or None)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic relation data."""

        return {
            "source_observation_id": self.source_observation_id,
            "target_observation_id": self.target_observation_id,
            "relation_type": self.relation_type.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class SituationSnapshot:
    """Immutable executive representation of a coherent situation."""

    situation_id: str
    title: str
    status: SituationStatus
    observations: tuple[Observation, ...]
    relations: tuple[SituationRelation, ...]
    opened_at: datetime
    updated_at: datetime
    confidence: float
    severity: ObservationSeverity
    mission_id: str | None = None
    correlation_id: str | None = None
    summary: str | None = None
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "situation_id",
            _required(self.situation_id, "situation_id"),
        )
        object.__setattr__(self, "title", _required(self.title, "title"))

        if not isinstance(self.status, SituationStatus):
            object.__setattr__(
                self,
                "status",
                SituationStatus(str(self.status)),
            )

        observations = tuple(
            _require_observation(item) for item in self.observations
        )
        if not observations:
            raise InvalidSituationError(
                "a situation must contain at least one observation"
            )

        ids = [item.observation_id for item in observations]
        if len(ids) != len(set(ids)):
            raise InvalidSituationError(
                "a situation cannot contain duplicate observation IDs"
            )

        object.__setattr__(
            self,
            "observations",
            tuple(sorted(observations, key=lambda item: item.observation_id)),
        )
        object.__setattr__(
            self,
            "relations",
            tuple(
                sorted(
                    self.relations,
                    key=lambda item: (
                        item.source_observation_id,
                        item.target_observation_id,
                        item.relation_type.value,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "opened_at",
            _utc(self.opened_at, "opened_at"),
        )
        object.__setattr__(
            self,
            "updated_at",
            _utc(self.updated_at, "updated_at"),
        )
        if self.updated_at < self.opened_at:
            raise InvalidSituationError(
                "updated_at must not be earlier than opened_at"
            )

        object.__setattr__(
            self,
            "confidence",
            _confidence(self.confidence),
        )

        if not isinstance(self.severity, ObservationSeverity):
            object.__setattr__(
                self,
                "severity",
                ObservationSeverity(str(self.severity)),
            )

        object.__setattr__(
            self,
            "labels",
            _label_pairs(dict(self.labels)),
        )

    @property
    def observation_ids(self) -> tuple[str, ...]:
        """Return the ordered observation identifiers."""

        return tuple(
            observation.observation_id
            for observation in self.observations
        )

    def label_map(self) -> dict[str, str]:
        """Return labels as a new dictionary."""

        return dict(self.labels)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic serialized situation data."""

        return {
            "situation_id": self.situation_id,
            "title": self.title,
            "status": self.status.value,
            "observations": [
                observation.to_canonical_dict()
                for observation in self.observations
            ],
            "relations": [
                relation.to_canonical_dict()
                for relation in self.relations
            ],
            "opened_at": self.opened_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence": self.confidence,
            "severity": self.severity.value,
            "mission_id": self.mission_id,
            "correlation_id": self.correlation_id,
            "summary": self.summary,
            "labels": self.label_map(),
        }

    def fingerprint(self) -> str:
        """Return the complete deterministic situation fingerprint."""

        return hashlib.sha256(
            _canonical_json(self.to_canonical_dict()).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class SituationQuery:
    """Repository query for situation snapshots."""

    status: SituationStatus | None = None
    mission_id: str | None = None
    correlation_id: str | None = None
    minimum_confidence: float | None = None
    minimum_severity: ObservationSeverity | None = None
    updated_from: datetime | None = None
    updated_to: datetime | None = None
    limit: int | None = None
    newest_first: bool = False

    def __post_init__(self) -> None:
        if self.minimum_confidence is not None:
            object.__setattr__(
                self,
                "minimum_confidence",
                _confidence(self.minimum_confidence),
            )
        if self.updated_from is not None:
            object.__setattr__(
                self,
                "updated_from",
                _utc(self.updated_from, "updated_from"),
            )
        if self.updated_to is not None:
            object.__setattr__(
                self,
                "updated_to",
                _utc(self.updated_to, "updated_to"),
            )
        if (
            self.updated_from is not None
            and self.updated_to is not None
            and self.updated_from > self.updated_to
        ):
            raise InvalidSituationError(
                "updated_from must not be after updated_to"
            )
        if self.limit is not None and self.limit < 1:
            raise InvalidSituationError("limit must be at least 1")


def derive_situation_identity(
    *,
    title: str,
    observations: Sequence[Observation],
    relations: Sequence[SituationRelation],
    mission_id: str | None,
    correlation_id: str | None,
) -> str:
    """Derive the stable semantic identity of a situation."""

    payload = {
        "title": _required(title, "title"),
        "observation_ids": sorted(
            _require_observation(item).observation_id
            for item in observations
        ),
        "relations": sorted(
            (
                relation.source_observation_id,
                relation.target_observation_id,
                relation.relation_type.value,
                relation.confidence,
                relation.rationale,
            )
            for relation in relations
        ),
        "mission_id": mission_id,
        "correlation_id": correlation_id,
    }
    return "sit_" + hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()


def derive_situation_confidence(
    observations: Sequence[Observation],
) -> float:
    """Return the arithmetic mean confidence of the observations."""

    normalized = tuple(_require_observation(item) for item in observations)
    if not normalized:
        raise InvalidSituationError(
            "confidence cannot be derived without observations"
        )
    return sum(item.confidence for item in normalized) / len(normalized)


def derive_situation_severity(
    observations: Sequence[Observation],
) -> ObservationSeverity:
    """Return the highest observation severity in the situation."""

    normalized = tuple(_require_observation(item) for item in observations)
    if not normalized:
        raise InvalidSituationError(
            "severity cannot be derived without observations"
        )
    return max(
        (item.severity for item in normalized),
        key=lambda item: _SEVERITY_RANK[item],
    )

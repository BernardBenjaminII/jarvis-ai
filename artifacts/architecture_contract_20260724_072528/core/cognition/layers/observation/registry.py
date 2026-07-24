from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Iterable
from uuid import UUID

from .errors import DuplicateObservationError, ObservationNotFoundError
from .models import ObservationRecord


class ObservationRegistry:
    """Thread-safe in-memory registry for certified observation records."""

    def __init__(self) -> None:
        self._records: dict[UUID, ObservationRecord] = {}
        self._hash_index: dict[str, UUID] = {}
        self._subject_index: dict[str, set[UUID]] = defaultdict(set)
        self._lock = RLock()

    def register(
        self,
        observation: ObservationRecord,
        *,
        replace_existing: bool = False,
    ) -> ObservationRecord:
        with self._lock:
            if (
                observation.observation_id in self._records
                and not replace_existing
            ):
                raise DuplicateObservationError(
                    f"Observation already registered: {observation.observation_id}"
                )

            self._records[observation.observation_id] = observation
            self._hash_index[observation.deterministic_hash] = (
                observation.observation_id
            )
            if observation.subject:
                self._subject_index[observation.subject].add(
                    observation.observation_id
                )
            return observation

    def get(self, observation_id: UUID) -> ObservationRecord:
        with self._lock:
            try:
                return self._records[observation_id]
            except KeyError as exc:
                raise ObservationNotFoundError(str(observation_id)) from exc

    def contains(self, observation_id: UUID) -> bool:
        with self._lock:
            return observation_id in self._records

    def find_by_hash(self, deterministic_hash: str) -> ObservationRecord | None:
        with self._lock:
            observation_id = self._hash_index.get(deterministic_hash)
            return (
                self._records.get(observation_id)
                if observation_id is not None
                else None
            )

    def find_by_subject(self, subject: str) -> tuple[ObservationRecord, ...]:
        with self._lock:
            ids = sorted(self._subject_index.get(subject, set()), key=str)
            return tuple(self._records[item] for item in ids)

    def all(self) -> tuple[ObservationRecord, ...]:
        with self._lock:
            return tuple(
                self._records[item]
                for item in sorted(self._records, key=str)
            )

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


__all__ = ("ObservationRegistry",)

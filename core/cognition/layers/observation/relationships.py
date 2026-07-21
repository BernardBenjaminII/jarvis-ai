from __future__ import annotations

from collections import defaultdict
from threading import RLock
from uuid import UUID

from .models import ObservationRelation


class ObservationRelationshipManager:
    def __init__(self) -> None:
        self._outgoing: dict[UUID, list[ObservationRelation]] = defaultdict(list)
        self._incoming: dict[UUID, list[ObservationRelation]] = defaultdict(list)
        self._lock = RLock()

    def add(self, relation: ObservationRelation) -> ObservationRelation:
        if relation.source_id == relation.target_id:
            raise ValueError("Self-relations are not permitted.")
        if not 0.0 <= relation.confidence <= 1.0:
            raise ValueError("Relation confidence must be within [0.0, 1.0].")

        with self._lock:
            if relation not in self._outgoing[relation.source_id]:
                self._outgoing[relation.source_id].append(relation)
                self._incoming[relation.target_id].append(relation)
        return relation

    def outgoing(self, observation_id: UUID) -> tuple[ObservationRelation, ...]:
        with self._lock:
            return tuple(self._outgoing.get(observation_id, ()))

    def incoming(self, observation_id: UUID) -> tuple[ObservationRelation, ...]:
        with self._lock:
            return tuple(self._incoming.get(observation_id, ()))


__all__ = ("ObservationRelationshipManager",)

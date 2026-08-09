"""Constitutional Executive Event Bus."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from threading import RLock
from typing import Callable
from uuid import uuid4

from core.executive.timeline import (
    ExecutiveTimelineEngine,
    ExecutiveTimelineRepository,
    TimelineEvent,
    TimelineEventDraft,
)
from core.executive.timeline.repository_contracts import (
    TimelineRepositoryConflictError,
)

from .contracts import (
    ExecutiveEventSubscriber,
    ExecutivePublication,
    ExecutiveSubscriberFailure,
)


@dataclass(frozen=True, slots=True)
class ExecutiveSubscription:
    """Opaque handle for one Event Bus subscription."""

    subscription_id: str
    subscriber_name: str


class ExecutiveEventBus:
    """
    Canonical synchronous publication boundary.

    Repository persistence is authoritative. A stale in-memory engine may be
    rejected by repository conflict detection; the bus then reloads the disk
    authority, rebuilds its engine, and retries the semantic draft once.
    """

    def __init__(
        self,
        *,
        repository: ExecutiveTimelineRepository,
        event_id_factory: Callable[[int], str] | None = None,
    ) -> None:
        self._repository = repository
        self._event_id_factory = event_id_factory
        self._engine = self._new_engine()
        self._subscribers: dict[
            str,
            tuple[str, ExecutiveEventSubscriber],
        ] = {}
        self._lock = RLock()

    @property
    def repository(self) -> ExecutiveTimelineRepository:
        return self._repository

    @property
    def events(self) -> tuple[TimelineEvent, ...]:
        return self._repository.events

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def subscribe(
        self,
        subscriber: ExecutiveEventSubscriber,
        *,
        name: str | None = None,
    ) -> ExecutiveSubscription:
        if not callable(subscriber):
            raise TypeError("subscriber must be callable.")

        subscription_id = str(uuid4())
        subscriber_name = (
            str(name).strip()
            if name is not None
            else getattr(
                subscriber,
                "__qualname__",
                getattr(
                    subscriber,
                    "__name__",
                    type(subscriber).__name__,
                ),
            )
        )

        if not subscriber_name:
            raise ValueError("subscriber name cannot be empty.")

        with self._lock:
            self._subscribers[subscription_id] = (
                subscriber_name,
                subscriber,
            )

        return ExecutiveSubscription(
            subscription_id=subscription_id,
            subscriber_name=subscriber_name,
        )

    def unsubscribe(
        self,
        subscription: ExecutiveSubscription | str,
    ) -> bool:
        subscription_id = (
            subscription.subscription_id
            if isinstance(subscription, ExecutiveSubscription)
            else str(subscription)
        )

        with self._lock:
            return (
                self._subscribers.pop(subscription_id, None)
                is not None
            )

    def publish(
        self,
        draft: TimelineEventDraft,
    ) -> ExecutivePublication:
        draft.validate()

        with self._lock:
            event = self._commit_with_stale_writer_retry(draft)
            subscribers = tuple(self._subscribers.items())

        delivered = 0
        failures: list[ExecutiveSubscriberFailure] = []

        for subscription_id, (
            subscriber_name,
            subscriber,
        ) in subscribers:
            try:
                subscriber(event)
                delivered += 1
            except Exception as exc:
                failures.append(
                    ExecutiveSubscriberFailure(
                        subscription_id=subscription_id,
                        subscriber_name=subscriber_name,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        return ExecutivePublication(
            event=event,
            delivered_subscribers=delivered,
            subscriber_failures=tuple(failures),
        )

    def _commit_with_stale_writer_retry(
        self,
        draft: TimelineEventDraft,
    ) -> TimelineEvent:
        for attempt in (1, 2):
            event = self._engine.append(draft)

            try:
                self._repository.append(event)
                return event
            except TimelineRepositoryConflictError:
                self._repository.reload()
                self._engine = self._new_engine()

                if attempt == 2:
                    raise

        raise RuntimeError("Unreachable Event Bus retry state.")

    def publish_many(
        self,
        drafts: Iterable[TimelineEventDraft],
    ) -> tuple[ExecutivePublication, ...]:
        return tuple(self.publish(draft) for draft in drafts)

    def latest(self, limit: int = 25) -> tuple[TimelineEvent, ...]:
        self._repository.reload()
        self._engine = self._new_engine()
        return self._repository.latest(limit=limit)

    def verify(self):
        self._repository.reload()
        self._engine = self._new_engine()
        return self._repository.verify()

    def _new_engine(self) -> ExecutiveTimelineEngine:
        return ExecutiveTimelineEngine(
            event_id_factory=self._event_id_factory,
            initial_events=self._repository.events,
        )

"""Contracts for the constitutional Executive Event Bus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.executive.timeline import TimelineEvent


@runtime_checkable
class ExecutiveEventSubscriber(Protocol):
    def __call__(self, event: TimelineEvent) -> None:
        """Observe one event after persistence succeeds."""


@dataclass(frozen=True, slots=True)
class ExecutiveSubscriberFailure:
    subscription_id: str
    subscriber_name: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ExecutivePublication:
    event: TimelineEvent
    delivered_subscribers: int
    subscriber_failures: tuple[ExecutiveSubscriberFailure, ...]

    @property
    def fully_delivered(self) -> bool:
        return not self.subscriber_failures

"""
Genesis VII-A0 Pack 2
Executive live-transport foundation.

This module provides:

- a subscriber-safe in-process broadcast broker;
- canonical WebSocket envelopes;
- periodic Executive dashboard publication;
- explicit shutdown semantics.

Pack 2 uses an in-process broker intentionally. A distributed broker may
replace it later without changing the public WebSocket contract.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from uuid import uuid4

from .services import ExecutiveDashboardService


def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 form."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class ExecutiveLiveEnvelope:
    """
    Canonical message transmitted through the Executive live channel.

    Message types established by Pack 2:

    - executive.connected
    - executive.dashboard
    - executive.heartbeat
    - executive.error
    """

    message_id: str
    message_type: str
    payload: dict[str, Any]
    published_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"

    @classmethod
    def create(
        cls,
        *,
        message_type: str,
        payload: dict[str, Any],
    ) -> "ExecutiveLiveEnvelope":
        return cls(
            message_id=str(uuid4()),
            message_type=message_type,
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutiveSubscription:
    """One isolated subscription to the Executive live broker."""

    def __init__(
        self,
        *,
        broker: "ExecutiveLiveBroker",
        subscription_id: str,
        queue: asyncio.Queue[ExecutiveLiveEnvelope],
    ) -> None:
        self._broker = broker
        self.subscription_id = subscription_id
        self._queue = queue
        self._closed = False

    async def receive(self) -> ExecutiveLiveEnvelope:
        """Wait for and return the next available message."""
        if self._closed:
            raise RuntimeError("Subscription is closed.")

        return await self._queue.get()

    async def messages(self) -> AsyncIterator[ExecutiveLiveEnvelope]:
        """Yield messages until the subscription is closed."""
        while not self._closed:
            yield await self.receive()

    async def close(self) -> None:
        """Remove this subscription from the broker."""
        if self._closed:
            return

        self._closed = True
        await self._broker.unsubscribe(self.subscription_id)

    async def __aenter__(self) -> "ExecutiveSubscription":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        await self.close()


class ExecutiveLiveBroker:
    """
    In-process fan-out broker for Executive WebSocket messages.

    Every subscriber receives an independent bounded queue. A slow or abandoned
    client therefore cannot block all other Executive clients.
    """

    def __init__(self, *, queue_size: int = 32) -> None:
        if queue_size < 1:
            raise ValueError("queue_size must be at least 1.")

        self._queue_size = queue_size
        self._subscriptions: dict[
            str,
            asyncio.Queue[ExecutiveLiveEnvelope],
        ] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self) -> ExecutiveSubscription:
        """Create and register an isolated subscription."""
        subscription_id = str(uuid4())
        queue: asyncio.Queue[ExecutiveLiveEnvelope] = asyncio.Queue(
            maxsize=self._queue_size
        )

        async with self._lock:
            self._subscriptions[subscription_id] = queue

        return ExecutiveSubscription(
            broker=self,
            subscription_id=subscription_id,
            queue=queue,
        )

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription when it exists."""
        async with self._lock:
            self._subscriptions.pop(subscription_id, None)

    async def publish(self, envelope: ExecutiveLiveEnvelope) -> int:
        """
        Publish a message to every current subscriber.

        When a subscriber queue is full, its oldest message is discarded so
        the client receives the newest available Executive state.
        """
        async with self._lock:
            subscribers = tuple(self._subscriptions.values())

        delivered = 0

        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            try:
                queue.put_nowait(envelope)
                delivered += 1
            except asyncio.QueueFull:
                # A concurrent producer may have filled the queue again.
                continue

        return delivered

    async def subscriber_count(self) -> int:
        """Return the current number of live subscribers."""
        async with self._lock:
            return len(self._subscriptions)


class ExecutiveSnapshotPublisher:
    """
    Periodically publish Executive dashboard snapshots.

    The publisher performs no work until `start()` is called. This keeps module
    imports deterministic and lets FastAPI lifespan control the task.
    """

    def __init__(
        self,
        *,
        dashboard_service: ExecutiveDashboardService,
        broker: ExecutiveLiveBroker,
        interval_seconds: float = 5.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")

        self._dashboard_service = dashboard_service
        self._broker = broker
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start the periodic publisher once."""
        if self.running:
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._run(),
            name="executive-dashboard-publisher",
        )

    async def stop(self) -> None:
        """Stop the periodic publisher and await clean termination."""
        self._stop_event.set()

        if self._task is None:
            return

        task = self._task
        self._task = None

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

    async def publish_once(
        self,
        *,
        force_refresh: bool = False,
    ) -> ExecutiveLiveEnvelope:
        """Collect and publish one current dashboard snapshot."""
        snapshot = await asyncio.to_thread(
            self._dashboard_service.snapshot,
            force_refresh=force_refresh,
        )

        envelope = ExecutiveLiveEnvelope.create(
            message_type="executive.dashboard",
            payload=snapshot.to_dict(),
        )
        await self._broker.publish(envelope)
        return envelope

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.publish_once(force_refresh=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                envelope = ExecutiveLiveEnvelope.create(
                    message_type="executive.error",
                    payload={
                        "component": "dashboard_publisher",
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    },
                )
                await self._broker.publish(envelope)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._interval_seconds,
                )
            except asyncio.TimeoutError:
                continue

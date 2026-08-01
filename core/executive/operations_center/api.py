"""
Genesis VII-A0 Pack 2
Executive Operations Center FastAPI router.

Public contract:

GET /operations/executive/dashboard
GET /operations/executive/health
GET /operations/executive/status
GET /operations/executive/metrics
GET /operations/executive/events
GET /operations/executive/live/status
WS  /operations/executive/live
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .models import MetricState
from .services import (
    ExecutiveDashboardService,
    ExecutiveHealthService,
    ExecutiveMetricsService,
    ExecutiveStatusService,
)
from .transport import (
    ExecutiveLiveBroker,
    ExecutiveLiveEnvelope,
    ExecutiveSnapshotPublisher,
)


EXECUTIVE_API_PREFIX = "/operations/executive"
EXECUTIVE_API_TAG = "Executive Operations Center"


@dataclass(slots=True)
class ExecutiveOperationsRuntime:
    """Long-lived Pack 2 services shared by REST and WebSocket handlers."""

    health_service: ExecutiveHealthService
    metrics_service: ExecutiveMetricsService
    status_service: ExecutiveStatusService
    dashboard_service: ExecutiveDashboardService
    broker: ExecutiveLiveBroker
    publisher: ExecutiveSnapshotPublisher


def _publisher_interval() -> float:
    raw_value = os.environ.get(
        "JARVIS_EXECUTIVE_LIVE_INTERVAL_SECONDS",
        "5.0",
    )

    try:
        value = float(raw_value)
    except ValueError:
        return 5.0

    return value if value > 0 else 5.0


def build_runtime() -> ExecutiveOperationsRuntime:
    """Build the canonical process-local Executive API runtime."""
    health_service = ExecutiveHealthService()
    metrics_service = ExecutiveMetricsService()
    status_service = ExecutiveStatusService()

    dashboard_service = ExecutiveDashboardService(
        health_service=health_service,
        metrics_service=metrics_service,
        status_service=status_service,
    )

    broker = ExecutiveLiveBroker()

    publisher = ExecutiveSnapshotPublisher(
        dashboard_service=dashboard_service,
        broker=broker,
        interval_seconds=_publisher_interval(),
    )

    return ExecutiveOperationsRuntime(
        health_service=health_service,
        metrics_service=metrics_service,
        status_service=status_service,
        dashboard_service=dashboard_service,
        broker=broker,
        publisher=publisher,
    )


runtime = build_runtime()

router = APIRouter(
    prefix=EXECUTIVE_API_PREFIX,
    tags=[EXECUTIVE_API_TAG],
)


def _transport_response(
    *,
    data: dict[str, Any],
    resource: str,
) -> dict[str, Any]:
    """Wrap API data in a stable Pack 2 transport envelope."""
    return {
        "ok": True,
        "resource": resource,
        "data": data,
        "transport_version": "1.0.0",
    }


@router.get("/dashboard")
async def executive_dashboard(
    refresh: bool = Query(
        default=False,
        description="Force collection instead of using the short live cache.",
    ),
) -> dict[str, Any]:
    snapshot = await asyncio.to_thread(
        runtime.dashboard_service.snapshot,
        force_refresh=refresh,
    )

    return _transport_response(
        resource="executive_dashboard",
        data=snapshot.to_dict(),
    )


@router.get("/health")
async def executive_health(
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    snapshot = await asyncio.to_thread(
        runtime.health_service.snapshot,
        force_refresh=refresh,
    )

    return _transport_response(
        resource="executive_health",
        data=snapshot.to_dict(),
    )


@router.get("/metrics")
async def executive_metrics(
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    snapshot = await asyncio.to_thread(
        runtime.metrics_service.snapshot,
        force_refresh=refresh,
    )

    return _transport_response(
        resource="executive_metrics",
        data=snapshot.to_dict(),
    )


@router.get("/status")
async def executive_status(
    refresh: bool = Query(default=False),
) -> dict[str, Any]:
    health = await asyncio.to_thread(
        runtime.health_service.snapshot,
        force_refresh=refresh,
    )
    metrics = await asyncio.to_thread(
        runtime.metrics_service.snapshot,
        force_refresh=refresh,
    )
    status = runtime.status_service.derive(
        health=health,
        metrics=metrics,
    )

    return _transport_response(
        resource="executive_status",
        data=status.to_dict(),
    )


@router.get("/events")
async def executive_events() -> dict[str, Any]:
    """
    Report the current Executive Event integration state.

    Pack 2 establishes the API contract but does not invent an event history.
    The authoritative Event Registry is connected in Pack 4.
    """
    metrics = await asyncio.to_thread(
        runtime.metrics_service.snapshot,
        force_refresh=False,
    )
    event_metric = metrics.metrics.get("executive_events")

    configured = (
        event_metric is not None
        and event_metric.state is not MetricState.NOT_CONFIGURED
    )

    return _transport_response(
        resource="executive_events",
        data={
            "integration_state": (
                event_metric.state.value
                if event_metric is not None
                else MetricState.NOT_CONFIGURED.value
            ),
            "configured": configured,
            "event_count": (
                event_metric.value
                if event_metric is not None
                else None
            ),
            "events": [],
            "message": (
                "The Executive Event Registry transport is established. "
                "Authoritative event retrieval is reserved for Pack 4."
            ),
            "schema_version": "1.0.0",
        },
    )


@router.get("/live/status")
async def executive_live_status() -> dict[str, Any]:
    return _transport_response(
        resource="executive_live_status",
        data={
            "publisher_running": runtime.publisher.running,
            "subscriber_count": await runtime.broker.subscriber_count(),
            "interval_seconds": _publisher_interval(),
            "websocket_path": f"{EXECUTIVE_API_PREFIX}/live",
            "schema_version": "1.0.0",
        },
    )


@router.websocket("/live")
async def executive_live(websocket: WebSocket) -> None:
    """
    Stream live Executive dashboard snapshots to one browser client.

    The connection receives an immediate connection envelope followed by an
    immediate dashboard snapshot. Further snapshots are supplied by the shared
    publisher or explicit publication calls.
    """
    await websocket.accept()
    subscription = await runtime.broker.subscribe()

    try:
        connected = ExecutiveLiveEnvelope.create(
            message_type="executive.connected",
            payload={
                "subscription_id": subscription.subscription_id,
                "websocket_path": f"{EXECUTIVE_API_PREFIX}/live",
                "schema_version": "1.0.0",
            },
        )
        await websocket.send_json(connected.to_dict())

        snapshot = await asyncio.to_thread(
            runtime.dashboard_service.snapshot,
            force_refresh=False,
        )
        initial = ExecutiveLiveEnvelope.create(
            message_type="executive.dashboard",
            payload=snapshot.to_dict(),
        )
        await websocket.send_json(initial.to_dict())

        while True:
            message_task = asyncio.create_task(subscription.receive())
            client_task = asyncio.create_task(websocket.receive())

            done, pending = await asyncio.wait(
                {message_task, client_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            for task in pending:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if client_task in done:
                client_message = client_task.result()
                message_type = client_message.get("type")

                if message_type == "websocket.disconnect":
                    return

                text = client_message.get("text")

                if text == "ping":
                    heartbeat = ExecutiveLiveEnvelope.create(
                        message_type="executive.heartbeat",
                        payload={"status": "alive"},
                    )
                    await websocket.send_json(heartbeat.to_dict())

            if message_task in done:
                envelope = message_task.result()
                await websocket.send_json(envelope.to_dict())

    except WebSocketDisconnect:
        return
    finally:
        await subscription.close()

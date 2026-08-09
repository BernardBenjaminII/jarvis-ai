"""Genesis VII-A0 Pack 4A-3 certification tests."""
from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from fastapi import FastAPI

from core.executive.events import (
    ExecutiveEventRuntimeState,
    build_executive_event_runtime,
    install_executive_event_runtime,
    resolve_operations_live_broker,
)
from core.executive.events.bus import ExecutiveEventBus
from core.executive.operations_center.transport import ExecutiveLiveBroker
from core.executive.timeline import ExecutiveTimelineRepository, TimelineEventKind


class GenesisVIIA0Pack4A3Tests(unittest.IsolatedAsyncioTestCase):
    def build_runtime(self, root: Path):
        bus = ExecutiveEventBus(
            repository=ExecutiveTimelineRepository(root),
            event_id_factory=lambda sequence: f"event-{sequence:04d}",
        )
        broker = ExecutiveLiveBroker(queue_size=8)
        return build_executive_event_runtime(
            live_broker=broker,
            event_bus=bus,
        )

    async def test_runtime_start_and_stop_publish_lifecycle(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = self.build_runtime(Path(directory))
            subscription = await runtime.live_broker.subscribe()

            await runtime.start()
            await asyncio.sleep(0)

            self.assertIs(
                runtime.state,
                ExecutiveEventRuntimeState.RUNNING,
            )
            self.assertTrue(runtime.live_bridge.active)
            self.assertEqual(
                [event.kind for event in runtime.event_bus.events],
                [
                    TimelineEventKind.EXECUTIVE_BOOT_STARTED,
                    TimelineEventKind.EXECUTIVE_BOOT_COMPLETED,
                ],
            )

            first_envelope = await asyncio.wait_for(
                subscription.receive(),
                timeout=1,
            )
            self.assertEqual(
                first_envelope.message_type,
                "executive.event",
            )

            await runtime.stop()
            self.assertIs(
                runtime.state,
                ExecutiveEventRuntimeState.STOPPED,
            )
            self.assertFalse(runtime.live_bridge.active)
            self.assertEqual(
                runtime.event_bus.events[-2].kind,
                TimelineEventKind.EXECUTIVE_SHUTDOWN_STARTED,
            )
            self.assertEqual(
                runtime.event_bus.events[-1].kind,
                TimelineEventKind.EXECUTIVE_SHUTDOWN_COMPLETED,
            )
            await subscription.close()

    async def test_runtime_start_is_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = self.build_runtime(Path(directory))

            await runtime.start()
            await runtime.start()

            self.assertEqual(len(runtime.event_bus.events), 2)
            await runtime.stop()

    async def test_fastapi_state_installation(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = self.build_runtime(Path(directory))
            app = FastAPI()

            install_executive_event_runtime(app, runtime)

            self.assertIs(
                app.state.executive_event_runtime,
                runtime,
            )
            self.assertIs(
                app.state.executive_event_bus,
                runtime.event_bus,
            )
            self.assertIs(
                app.state.executive_timeline_repository,
                runtime.event_bus.repository,
            )

    async def test_operations_broker_resolution(self) -> None:
        broker = ExecutiveLiveBroker()
        self.assertIs(
            resolve_operations_live_broker(
                SimpleNamespace(broker=broker)
            ),
            broker,
        )
        self.assertIs(
            resolve_operations_live_broker(
                SimpleNamespace(live_broker=broker)
            ),
            broker,
        )

    async def test_runtime_snapshot_is_certified(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = self.build_runtime(Path(directory))
            await runtime.start()

            snapshot = runtime.snapshot()

            self.assertEqual(snapshot.state.value, "running")
            self.assertEqual(snapshot.event_count, 2)
            self.assertTrue(snapshot.bridge_active)
            self.assertTrue(snapshot.integrity_certified)
            await runtime.stop()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import asyncio
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.executive.operations_center.api import (
    EXECUTIVE_API_PREFIX,
    router,
    runtime,
)
from core.executive.operations_center.transport import (
    ExecutiveLiveBroker,
    ExecutiveLiveEnvelope,
)


def create_test_application() -> FastAPI:
    application = FastAPI()
    application.include_router(router)
    return application


class ExecutiveLiveBrokerTests(unittest.IsolatedAsyncioTestCase):
    async def test_broker_delivers_to_every_subscriber(self) -> None:
        broker = ExecutiveLiveBroker(queue_size=4)

        first = await broker.subscribe()
        second = await broker.subscribe()

        envelope = ExecutiveLiveEnvelope.create(
            message_type="executive.test",
            payload={"value": 7},
        )

        delivered = await broker.publish(envelope)

        self.assertEqual(delivered, 2)
        self.assertEqual((await first.receive()).payload["value"], 7)
        self.assertEqual((await second.receive()).payload["value"], 7)

        await first.close()
        await second.close()

        self.assertEqual(await broker.subscriber_count(), 0)

    async def test_broker_discards_oldest_message_when_queue_is_full(
        self,
    ) -> None:
        broker = ExecutiveLiveBroker(queue_size=1)
        subscription = await broker.subscribe()

        first = ExecutiveLiveEnvelope.create(
            message_type="executive.test",
            payload={"sequence": 1},
        )
        second = ExecutiveLiveEnvelope.create(
            message_type="executive.test",
            payload={"sequence": 2},
        )

        await broker.publish(first)
        await broker.publish(second)

        received = await subscription.receive()

        self.assertEqual(received.payload["sequence"], 2)
        await subscription.close()


class ExecutiveApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_test_application())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def test_dashboard_endpoint(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/dashboard"
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["resource"],
            "executive_dashboard",
        )
        self.assertIn("health", payload["data"])
        self.assertIn("metrics", payload["data"])
        self.assertIn("status", payload["data"])

    def test_health_endpoint(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/health"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["resource"],
            "executive_health",
        )

    def test_metrics_endpoint(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/metrics"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("metrics", response.json()["data"])

    def test_status_endpoint(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/status"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("overall_state", response.json()["data"])

    def test_events_endpoint_does_not_fabricate_events(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/events"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(data["events"], [])
        self.assertIn("integration_state", data)
        self.assertIn("configured", data)

    def test_live_status_endpoint(self) -> None:
        response = self.client.get(
            f"{EXECUTIVE_API_PREFIX}/live/status"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(
            data["websocket_path"],
            f"{EXECUTIVE_API_PREFIX}/live",
        )
        self.assertIn("subscriber_count", data)

    def test_websocket_receives_connection_and_dashboard(self) -> None:
        with self.client.websocket_connect(
            f"{EXECUTIVE_API_PREFIX}/live"
        ) as websocket:
            connected = websocket.receive_json()
            dashboard = websocket.receive_json()

            self.assertEqual(
                connected["message_type"],
                "executive.connected",
            )
            self.assertEqual(
                dashboard["message_type"],
                "executive.dashboard",
            )
            self.assertIn("health", dashboard["payload"])
            self.assertIn("metrics", dashboard["payload"])
            self.assertIn("status", dashboard["payload"])

    def test_websocket_ping_returns_heartbeat(self) -> None:
        with self.client.websocket_connect(
            f"{EXECUTIVE_API_PREFIX}/live"
        ) as websocket:
            websocket.receive_json()
            websocket.receive_json()

            websocket.send_text("ping")
            heartbeat = websocket.receive_json()

            self.assertEqual(
                heartbeat["message_type"],
                "executive.heartbeat",
            )
            self.assertEqual(
                heartbeat["payload"]["status"],
                "alive",
            )

    def test_explicit_broker_publication_reaches_websocket(self) -> None:
        with self.client.websocket_connect(
            f"{EXECUTIVE_API_PREFIX}/live"
        ) as websocket:
            websocket.receive_json()
            websocket.receive_json()

            envelope = ExecutiveLiveEnvelope.create(
                message_type="executive.test",
                payload={"certified": True},
            )

            asyncio.run(runtime.broker.publish(envelope))

            published = websocket.receive_json()

            self.assertEqual(
                published["message_type"],
                "executive.test",
            )
            self.assertTrue(published["payload"]["certified"])


if __name__ == "__main__":
    unittest.main()

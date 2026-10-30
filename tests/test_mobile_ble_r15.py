"""JARVIS BLE R1.5 watchdog integration tests.

All Bluetooth interactions are mocked. No physical adapters
or real iPhone connections are used.
"""

from types import SimpleNamespace
import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "tools/mobile_sensor"
BRIDGE_FILE = BRIDGE_DIR / "ble_bridge.py"

# Reproduce the import path used when systemd launches ble_bridge.py.
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

spec = importlib.util.spec_from_file_location(
    "jarvis_ble_r15_test_module", BRIDGE_FILE
)
ble = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = ble
spec.loader.exec_module(ble)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeClient:
    instances = []

    def __init__(self, *args, **kwargs):
        self.is_connected = False
        self.notifications = None
        self.stopped = False
        self.closed = False
        self.__class__.instances.append(self)

    async def __aenter__(self):
        self.is_connected = True
        return self

    async def __aexit__(self, *args):
        self.is_connected = False
        self.closed = True

    async def read_gatt_char(self, uuid):
        return b'{"test":true}'

    async def start_notify(self, uuid, callback):
        self.notifications = callback

    async def stop_notify(self, uuid):
        self.stopped = True

    async def write_gatt_char(self, *args, **kwargs):
        return None


def make_bridge():
    bridge = ble.JarvisBLEBridge(
        name="JarvisSensorNode",
        api_url="http://127.0.0.1:8000/test",
        token=None,
        scan_timeout=1.0,
        reconnect_delay=0.1,
        queue_size=10,
    )
    # Shorten timeouts for tests only.
    bridge.initial_grace = 0.15
    bridge.telemetry_timeout = 0.1
    return bridge


async def run_session(bridge, inject_frame=False):
    FakeClient.instances.clear()

    with (
        patch.object(ble, "BleakClient", FakeClient),
        patch.object(ble, "resolve", return_value="hci1"),
        patch.object(ble.asyncio, "sleep", wraps=asyncio.sleep),
    ):
        # Use a valid mock device: FakeClient ignores its identity.
        task = asyncio.create_task(
            bridge.connect_once(
                SimpleNamespace(
                    name="JarvisSensorNode",
                    address="AA:BB:CC:DD:EE:FF",
                )
            )
        )

        if inject_frame:
            await asyncio.sleep(0.03)
            # Update the frame timestamp to simulate accepted telemetry.
            bridge.last_frame_at = ble.time.monotonic()

        await asyncio.wait_for(task, timeout=3.0)

    assert FakeClient.instances
    return FakeClient.instances[-1]


@pytest.mark.anyio
async def test_initial_silence_triggers_watchdog():
    bridge = make_bridge()
    client = await run_session(bridge)

    assert client.closed
    assert client.stopped
    assert bridge.last_frame_at == 0.0


@pytest.mark.anyio
async def test_stream_stall_triggers_watchdog():
    bridge = make_bridge()
    client = await run_session(bridge, inject_frame=True)

    assert bridge.last_frame_at > 0.0
    assert client.closed
    assert client.stopped


@pytest.mark.anyio
async def test_normal_disconnect_exits_session():
    bridge = make_bridge()
    bridge.initial_grace = 2.0

    FakeClient.instances.clear()

    with (
        patch.object(ble, "BleakClient", FakeClient),
        patch.object(ble, "resolve", return_value="hci1"),
    ):
        task = asyncio.create_task(
            bridge.connect_once(
                SimpleNamespace(
                    name="JarvisSensorNode",
                    address="AA:BB:CC:DD:EE:FF",
                )
            )
        )

        await asyncio.sleep(0.05)
        bridge.disconnected_event.set()
        await asyncio.wait_for(task, timeout=3.0)

    assert FakeClient.instances[-1].closed

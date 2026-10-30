#!/usr/bin/env python3
"""
JARVIS BLE R1 bridge

iPhone JarvisSensorNode (CoreBluetooth peripheral)
    -> BLE telemetry notifications (schema-v3 NDJSON)
    -> this bridge on Xperion
    -> existing POST /api/sensors/mobile/telemetry

The backend/UI do not need to know whether telemetry arrived by USB or BLE.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from usb_bridge import normalize

from bleak import BleakClient, BleakScanner
# Ensure repository root is importable under systemd.
import sys
from pathlib import Path

JARVIS_ROOT = Path(__file__).resolve().parents[2]
if str(JARVIS_ROOT) not in sys.path:
    sys.path.insert(0, str(JARVIS_ROOT))

from tools.bluetooth.resolve_adapter import resolve
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


SERVICE_UUID = "8e7a0001-3b7f-4e0b-9f1a-4a5256495301"
TELEMETRY_UUID = "8e7a0002-3b7f-4e0b-9f1a-4a5256495302"
COMMAND_UUID = "8e7a0003-3b7f-4e0b-9f1a-4a5256495303"
STATUS_UUID = "8e7a0004-3b7f-4e0b-9f1a-4a5256495304"
CAPABILITIES_UUID = "8e7a0005-3b7f-4e0b-9f1a-4a5256495305"

DEFAULT_NAME = "JarvisSensorNode"
DEFAULT_API = "http://127.0.0.1:8000/api/sensors/mobile/telemetry"


@dataclass
class Metrics:
    notifications: int = 0
    bytes_rx: int = 0
    frames_rx: int = 0
    frames_forwarded: int = 0
    parse_errors: int = 0
    post_errors: int = 0
    queue_drops: int = 0
    connected_at: float = 0.0


class ApiForwarder:
    def __init__(self, api_url: str, token: str | None, timeout: float = 3.0):
        self.api_url = api_url
        self.token = token
        self.timeout = timeout

    def _post_sync(self, payload: bytes) -> tuple[int, bytes]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "jarvis-ble-r1/1.0",
        }
        if self.token:
            headers["X-Jarvis-Token"] = self.token

        req = urllib.request.Request(
            self.api_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return int(resp.status), resp.read(2048)

    async def post(self, payload: bytes) -> tuple[int, bytes]:
        return await asyncio.to_thread(self._post_sync, payload)


class JarvisBLEBridge:
    def __init__(
        self,
        *,
        name: str,
        api_url: str,
        token: str | None,
        scan_timeout: float,
        reconnect_delay: float,
        queue_size: int,
    ):
        self.name = name
        self.scan_timeout = scan_timeout
        self.reconnect_delay = reconnect_delay
        self.forwarder = ApiForwarder(api_url, token)
        self.metrics = Metrics()
        self.queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=queue_size)
        self.rx_buffer = bytearray()
        self.stop_event = asyncio.Event()
        self.disconnected_event = asyncio.Event()
        self.last_frame_at = 0.0
        self.session_started_at = 0.0
        self.telemetry_timeout = 15.0
        self.initial_grace = 20.0
        self._last_metric_log = 0.0

    def request_stop(self) -> None:
        self.stop_event.set()
        self.disconnected_event.set()

    async def find_node(self) -> tuple[BLEDevice, AdvertisementData] | None:
        logging.info("Scanning %.1fs for %s ...", self.scan_timeout, self.name)
        discovered = await BleakScanner.discover(
            timeout=self.scan_timeout,
            return_adv=True,
            bluez={"adapter": resolve("mobile_sensor")},
        )

        best: tuple[BLEDevice, AdvertisementData] | None = None
        for _, pair in discovered.items():
            device, adv = pair
            local_name = adv.local_name or device.name or ""
            service_uuids = {u.lower() for u in (adv.service_uuids or [])}
            name_match = local_name == self.name or self.name.lower() in local_name.lower()
            service_match = SERVICE_UUID.lower() in service_uuids

            if service_match and name_match:
                logging.info(
                    "Found exact node: name=%s address=%s rssi=%s",
                    local_name, device.address, adv.rssi,
                )
                return device, adv

            if service_match or name_match:
                best = pair

        if best:
            device, adv = best
            logging.info(
                "Found candidate node: name=%s address=%s rssi=%s services=%s",
                adv.local_name or device.name,
                device.address,
                adv.rssi,
                adv.service_uuids,
            )
        return best

    def _on_disconnect(self, _client: BleakClient) -> None:
        logging.warning("BLE disconnected")
        self.disconnected_event.set()

    def _on_telemetry(self, _sender, data: bytearray) -> None:
        self.metrics.notifications += 1
        self.metrics.bytes_rx += len(data)
        self.rx_buffer.extend(data)

        # Same wire contract as USB: one JSON object terminated by '\n'.
        while True:
            try:
                newline = self.rx_buffer.index(0x0A)
            except ValueError:
                break

            raw = bytes(self.rx_buffer[:newline]).strip()
            del self.rx_buffer[: newline + 1]

            if not raw:
                continue

            try:
                packet = json.loads(raw)

                # JARVIS_R15_FRAME_DIAGNOSTIC
                if self.metrics.frames_rx % 30 == 0:
                    fields = (
                        "accelerometerObservedAt",
                        "accelerometerXG",
                        "gyroObservedAt",
                        "gyroXRadPerSecond",
                        "magnetometerObservedAt",
                        "magnetometerXMicrotesla",
                        "motionObservedAt",
                        "rollRadians",
                        "barometerObservedAt",
                        "pressureKPa",
                        "absoluteAltitudeObservedAt",
                        "absoluteAltitudeMeters",
                    )
                    logging.info(
                        "R1.5 sensor fields: %s",
                        {
                            key: (
                                "populated"
                                if packet.get(key) is not None
                                else "null_or_missing"
                            )
                            for key in fields
                        },
                    )

                # Reuse the existing USB schema-v3 normalizer.
                normalized = normalize(packet)
                encoded = json.dumps(
                    normalized,
                    separators=(",", ":"),
                ).encode("utf-8")

            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                self.metrics.parse_errors += 1
                logging.error(
                    "Invalid telemetry frame (%s): %r",
                    exc,
                    raw[:240],
                )
                continue

            self.metrics.frames_rx += 1
            self.last_frame_at = time.monotonic()
            try:
                self.queue.put_nowait(encoded)
            except asyncio.QueueFull:
                self.metrics.queue_drops += 1
                # Prefer current telemetry over stale queued telemetry.
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    pass
                try:
                    self.queue.put_nowait(encoded)
                except asyncio.QueueFull:
                    pass

    async def forward_worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                raw = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                status, body = await self.forwarder.post(raw)
                if 200 <= status < 300:
                    self.metrics.frames_forwarded += 1
                else:
                    self.metrics.post_errors += 1
                    logging.error("API returned HTTP %s: %r", status, body[:240])
            except urllib.error.HTTPError as exc:
                self.metrics.post_errors += 1
                body = exc.read(1024) if hasattr(exc, "read") else b""
                logging.error("API HTTP error %s: %r", exc.code, body)
            except Exception:
                self.metrics.post_errors += 1
                logging.exception("Failed forwarding telemetry")
            finally:
                self.queue.task_done()

    async def metric_worker(self) -> None:
        previous_frames = 0
        previous_bytes = 0
        previous_time = time.monotonic()

        while not self.stop_event.is_set():
            await asyncio.sleep(5.0)
            now = time.monotonic()
            dt = max(now - previous_time, 0.001)
            fps = (self.metrics.frames_rx - previous_frames) / dt
            bps = (self.metrics.bytes_rx - previous_bytes) / dt

            logging.info(
                "BLE RX %.1f frames/s %.0f B/s | frames=%d forwarded=%d "
                "parse_err=%d post_err=%d drops=%d queue=%d",
                fps,
                bps,
                self.metrics.frames_rx,
                self.metrics.frames_forwarded,
                self.metrics.parse_errors,
                self.metrics.post_errors,
                self.metrics.queue_drops,
                self.queue.qsize(),
            )

            previous_frames = self.metrics.frames_rx
            previous_bytes = self.metrics.bytes_rx
            previous_time = now

    async def connect_once(self, device: BLEDevice) -> None:
        self.disconnected_event.clear()
        self.rx_buffer.clear()

        logging.info("Connecting to %s (%s) ...", device.name, device.address)
        async with BleakClient(
            device,
            disconnected_callback=self._on_disconnect,
            bluez={"adapter": resolve("mobile_sensor")},
        ) as client:
            if not client.is_connected:
                raise RuntimeError("BleakClient returned without a connection")

            self.metrics.connected_at = time.time()
            self.session_started_at = time.monotonic()
            self.last_frame_at = 0.0
            logging.info("BLE connected")

            # Read-only handshake first. Failure here is useful: it proves whether
            # the iPhone published the expected Jarvis service/characteristics.
            try:
                caps = bytes(await client.read_gatt_char(CAPABILITIES_UUID))
                logging.info("Capabilities: %s", caps.decode("utf-8", "replace"))
            except Exception:
                logging.exception("Could not read BLE capabilities")
                raise

            try:
                status = bytes(await client.read_gatt_char(STATUS_UUID))
                logging.info("Status: %s", status.decode("utf-8", "replace"))
            except Exception:
                logging.exception("Could not read BLE status")
                raise

            await client.start_notify(TELEMETRY_UUID, self._on_telemetry)
            logging.info("Subscribed to telemetry notifications")

            try:
                await client.write_gatt_char(
                    COMMAND_UUID,
                    b'{"cmd":"ping","source":"xperion"}\n',
                    response=True,
                )
                logging.info("PING command written")
            except Exception:
                logging.exception("Command-channel PING failed")
                raise

            logging.info("BLE R1 stream active; forwarding to existing Jarvis API")

            while (
                client.is_connected
                and not self.stop_event.is_set()
                and not self.disconnected_event.is_set()
            ):
                now = time.monotonic()
                reference = self.last_frame_at or self.session_started_at
                timeout = (
                    self.telemetry_timeout
                    if self.last_frame_at
                    else self.initial_grace
                )

                if reference and now - reference > timeout:
                    logging.warning(
                        "BLE TELEMETRY STALL: %.1fs without valid frames; "
                        "reconnecting",
                        now - reference,
                    )
                    break

                await asyncio.sleep(0.5)

            if client.is_connected:
                try:
                    await client.stop_notify(TELEMETRY_UUID)
                except Exception:
                    pass

    async def run(self) -> None:
        workers = [
            asyncio.create_task(self.forward_worker(), name="api-forwarder"),
            asyncio.create_task(self.metric_worker(), name="metrics"),
        ]

        try:
            while not self.stop_event.is_set():
                candidate = await self.find_node()
                if candidate is None:
                    logging.warning(
                        "No %s found. Keep the iPhone app open and BLE advertising.",
                        self.name,
                    )
                    await asyncio.sleep(self.reconnect_delay)
                    continue

                device, _adv = candidate
                try:
                    await self.connect_once(device)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logging.exception("BLE session failed")

                if not self.stop_event.is_set():
                    logging.info("Reconnecting in %.1fs ...", self.reconnect_delay)
                    await asyncio.sleep(self.reconnect_delay)
        finally:
            self.stop_event.set()
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="JARVIS iPhone BLE telemetry bridge")
    p.add_argument("--name", default=os.getenv("JARVIS_BLE_NAME", DEFAULT_NAME))
    p.add_argument("--api-url", default=os.getenv("JARVIS_MOBILE_API", DEFAULT_API))
    p.add_argument("--token", default=os.getenv("JARVIS_TOKEN"))
    p.add_argument("--scan-timeout", type=float, default=8.0)
    p.add_argument("--reconnect-delay", type=float, default=2.0)
    p.add_argument("--queue-size", type=int, default=512)
    p.add_argument("--verbose", action="store_true")
    return p


async def async_main(args: argparse.Namespace) -> None:
    bridge = JarvisBLEBridge(
        name=args.name,
        api_url=args.api_url,
        token=args.token,
        scan_timeout=args.scan_timeout,
        reconnect_delay=args.reconnect_delay,
        queue_size=args.queue_size,
    )

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, bridge.request_stop)
        except NotImplementedError:
            pass

    await bridge.run()


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        asyncio.run(async_main(args))
        return 0
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

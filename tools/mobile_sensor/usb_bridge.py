#!/usr/bin/env python3

import json
import os
import socket
import time
import urllib.error
import urllib.request


USB_HOST = "127.0.0.1"
USB_PORT = 8765

JARVIS_URL = (
    "http://127.0.0.1:8000"
    "/api/sensors/mobile/telemetry"
)

TOKEN = os.getenv("JARVIS_MOBILE_SENSOR_TOKEN")


def normalize(packet):
    """
    Translate JarvisSensorNode's Swift JSON schema
    into the Jarvis mobile-sensor API schema.
    """

    node_id = packet.get("nodeId")

    if not node_id:
        raise ValueError("packet missing nodeId")

    location = {
        "latitude": packet.get("latitude"),
        "longitude": packet.get("longitude"),
    }

    optional_location = {
        "altitude_m":
            packet.get("altitudeMeters"),

        "horizontal_accuracy_m":
            packet.get("horizontalAccuracyMeters"),

        "speed_mps":
            packet.get("speedMetersPerSecond"),
    }

    for key, value in optional_location.items():
        if value is not None:
            location[key] = value

    payload = {
        "node_id": node_id,

        "schema_version":
            packet.get("schemaVersion", 1),

        "sent_at":
            packet.get("sentAt")
            or packet.get("timestamp"),

        "observed_at":
            packet.get("locationObservedAt")
            or packet.get("timestamp"),

        "location": location,

        "device": {
            "platform": "ios",
            "transport": "usb",
            "source": "JarvisSensorNode",
        },
    }

    return payload


def post_to_jarvis(payload):

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        JARVIS_URL,
        data=body,
        method="POST",
    )

    request.add_header(
        "Content-Type",
        "application/json",
    )

    if TOKEN:
        request.add_header(
            "X-Jarvis-Token",
            TOKEN,
        )

    try:

        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:

            result = response.read().decode(
                "utf-8"
            )

            return response.status, result

    except urllib.error.HTTPError as exc:

        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        return exc.code, body


def run():

    print(
        f"[bridge] USB source "
        f"{USB_HOST}:{USB_PORT}"
    )

    print(
        f"[bridge] Jarvis target "
        f"{JARVIS_URL}"
    )

    while True:

        try:

            print(
                "[bridge] connecting to "
                "JarvisSensorNode..."
            )

            with socket.create_connection(
                (USB_HOST, USB_PORT),
                timeout=10,
            ) as sock:

                # The 10-second timeout is only for establishing
                # the connection. Once connected, wait indefinitely
                # for telemetry instead of dropping a healthy USB link.
                sock.settimeout(None)

                print(
                    "[bridge] USB tunnel connected; "
                    "waiting for iPhone telemetry..."
                )

                file = sock.makefile(
                    "r",
                    encoding="utf-8",
                )

                telemetry_active = False

                for line in file:

                    line = line.strip()

                    if not line:
                        continue

                    if not telemetry_active:
                        print(
                            "[bridge] iPhone telemetry active"
                        )
                        telemetry_active = True

                    try:

                        iphone_packet = json.loads(
                            line
                        )

                        payload = normalize(
                            iphone_packet
                        )

                        status, response = (
                            post_to_jarvis(
                                payload
                            )
                        )

                        lat = (
                            payload["location"]
                            .get("latitude")
                        )

                        lon = (
                            payload["location"]
                            .get("longitude")
                        )

                        print(
                            f"[bridge] HTTP {status} "
                            f"lat={lat} lon={lon} "
                            f"{response}"
                        )

                    except Exception as exc:

                        print(
                            "[bridge] packet error:",
                            exc,
                        )

        except (
            ConnectionRefusedError,
            ConnectionResetError,
            socket.timeout,
            OSError,
        ) as exc:

            print(
                "[bridge] USB unavailable:",
                exc,
            )

        print(
            "[bridge] reconnecting in 2s..."
        )

        time.sleep(2)


if __name__ == "__main__":
    run()

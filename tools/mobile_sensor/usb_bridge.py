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


def compact(mapping):
    return {
        key: value
        for key, value in mapping.items()
        if value is not None
    }


def normalize(packet):
    """
    Translate JarvisSensorNode Swift schema v1/v2/v3
    into the Jarvis mobile-sensor API schema.

    R3 preserves independent timestamps for GNSS, heading,
    IMU, barometer, activity, pedometer, and device state.
    """

    node_id = packet.get("nodeId")

    if not node_id:
        raise ValueError("packet missing nodeId")

    location = compact({
        "latitude":
            packet.get("latitude"),

        "longitude":
            packet.get("longitude"),

        "altitude_m":
            packet.get("altitudeMeters"),

        "horizontal_accuracy_m":
            packet.get("horizontalAccuracyMeters"),

        "vertical_accuracy_m":
            packet.get("verticalAccuracyMeters"),

        "speed_mps":
            packet.get("speedMetersPerSecond"),

        "speed_accuracy_mps":
            packet.get("speedAccuracyMetersPerSecond"),

        "course_deg":
            packet.get("courseDegrees"),

        "course_accuracy_deg":
            packet.get("courseAccuracyDegrees"),
    })

    heading = compact({
        "observed_at":
            packet.get("headingObservedAt"),

        "magnetic_deg":
            packet.get("magneticHeadingDegrees"),

        "true_deg":
            packet.get("trueHeadingDegrees"),

        "accuracy_deg":
            packet.get("headingAccuracyDegrees"),
    })

    raw_accelerometer = compact({
        "observed_at":
            packet.get("accelerometerObservedAt"),

        "x_g":
            packet.get("accelerometerXG"),

        "y_g":
            packet.get("accelerometerYG"),

        "z_g":
            packet.get("accelerometerZG"),
    })

    raw_gyro = compact({
        "observed_at":
            packet.get("gyroObservedAt"),

        "x_rad_s":
            packet.get("gyroXRadPerSecond"),

        "y_rad_s":
            packet.get("gyroYRadPerSecond"),

        "z_rad_s":
            packet.get("gyroZRadPerSecond"),
    })

    raw_magnetometer = compact({
        "observed_at":
            packet.get("magnetometerObservedAt"),

        "x_uT":
            packet.get("magnetometerXMicrotesla"),

        "y_uT":
            packet.get("magnetometerYMicrotesla"),

        "z_uT":
            packet.get("magnetometerZMicrotesla"),
    })

    attitude = compact({
        "roll_rad":
            packet.get("rollRadians"),

        "pitch_rad":
            packet.get("pitchRadians"),

        "yaw_rad":
            packet.get("yawRadians"),
    })

    gravity = compact({
        "x_g":
            packet.get("gravityXG"),

        "y_g":
            packet.get("gravityYG"),

        "z_g":
            packet.get("gravityZG"),
    })

    user_acceleration = compact({
        "x_g":
            packet.get("userAccelerationXG"),

        "y_g":
            packet.get("userAccelerationYG"),

        "z_g":
            packet.get("userAccelerationZG"),
    })

    rotation_rate = compact({
        "x_rad_s":
            packet.get("rotationRateXRadPerSecond"),

        "y_rad_s":
            packet.get("rotationRateYRadPerSecond"),

        "z_rad_s":
            packet.get("rotationRateZRadPerSecond"),
    })

    calibrated_magnetic = compact({
        "x_uT":
            packet.get("calibratedMagneticXMicrotesla"),

        "y_uT":
            packet.get("calibratedMagneticYMicrotesla"),

        "z_uT":
            packet.get("calibratedMagneticZMicrotesla"),

        "accuracy":
            packet.get("calibratedMagneticAccuracy"),
    })

    motion = compact({
        "observed_at":
            packet.get("motionObservedAt"),

        "attitude":
            attitude or None,

        "gravity":
            gravity or None,

        "user_acceleration":
            user_acceleration or None,

        "rotation_rate":
            rotation_rate or None,

        "calibrated_magnetic_field":
            calibrated_magnetic or None,
    })

    environment = compact({
        "barometer_observed_at":
            packet.get("barometerObservedAt"),

        "pressure_kpa":
            packet.get("pressureKPa"),

        "relative_altitude_m":
            packet.get("relativeAltitudeMeters"),

        "absolute_altitude_observed_at":
            packet.get("absoluteAltitudeObservedAt"),

        "absolute_altitude_m":
            packet.get("absoluteAltitudeMeters"),

        "absolute_altitude_accuracy_m":
            packet.get("absoluteAltitudeAccuracyMeters"),

        "absolute_altitude_precision_m":
            packet.get("absoluteAltitudePrecisionMeters"),
    })

    activity = compact({
        "observed_at":
            packet.get("activityObservedAt"),

        "stationary":
            packet.get("activityStationary"),

        "walking":
            packet.get("activityWalking"),

        "running":
            packet.get("activityRunning"),

        "automotive":
            packet.get("activityAutomotive"),

        "cycling":
            packet.get("activityCycling"),

        "unknown":
            packet.get("activityUnknown"),

        "confidence":
            packet.get("activityConfidence"),
    })

    pedometer = compact({
        "observed_at":
            packet.get("pedometerObservedAt"),

        "steps":
            packet.get("stepCount"),

        "distance_m":
            packet.get("walkingDistanceMeters"),

        "floors_ascended":
            packet.get("floorsAscended"),

        "floors_descended":
            packet.get("floorsDescended"),

        "current_pace_s_per_m":
            packet.get("currentPaceSecondsPerMeter"),

        "current_cadence_steps_per_s":
            packet.get("currentCadenceStepsPerSecond"),

        "average_active_pace_s_per_m":
            packet.get("averageActivePaceSecondsPerMeter"),
    })

    device = compact({
        "platform":
            "ios",

        "transport":
            "usb",

        "source":
            "JarvisSensorNode",

        "observed_at":
            packet.get("deviceObservedAt"),

        "battery_level":
            packet.get("batteryLevel"),

        "battery_state":
            packet.get("batteryState"),

        "thermal_state":
            packet.get("thermalState"),

        "proximity_near":
            packet.get("proximityNear"),

        "model":
            packet.get("deviceModel"),

        "system_name":
            packet.get("systemName"),

        "system_version":
            packet.get("systemVersion"),
    })

    raw = compact({
        "accelerometer":
            raw_accelerometer or None,

        "gyroscope":
            raw_gyro or None,

        "magnetometer":
            raw_magnetometer or None,
    })

    payload = {
        "node_id": node_id,

        "schema_version":
            packet.get("schemaVersion", 1),

        "sent_at":
            packet.get("sentAt")
            or packet.get("timestamp"),

        # Preserve GNSS freshness separately from transport freshness.
        "observed_at":
            packet.get("locationObservedAt")
            or packet.get("timestamp"),

        "location": location,

        "device": device,
    }

    optional_blocks = {
        "capabilities":
            packet.get("capabilities"),

        "heading":
            heading,

        "motion":
            motion,

        "raw":
            raw,

        "environment":
            environment,

        "activity":
            activity,

        "pedometer":
            pedometer,
    }

    for key, value in optional_blocks.items():
        if value:
            payload[key] = value

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

                        blocks = [
                            key
                            for key in (
                                "heading",
                                "motion",
                                "raw",
                                "environment",
                                "activity",
                                "pedometer",
                            )
                            if key in payload
                        ]

                        print(
                            f"[bridge] HTTP {status} "
                            f"schema={payload.get('schema_version')} "
                            f"lat={lat} lon={lon} "
                            f"blocks={','.join(blocks) or '-'} "
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

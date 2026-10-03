from __future__ import annotations

from pathlib import Path

from core.capabilities.adapters.local_sensors import mobile


def _isolated_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        mobile,
        "_STATE_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        mobile,
        "_LATEST",
        tmp_path / "latest.json",
    )

    monkeypatch.setattr(
        mobile,
        "_STALE_SECONDS",
        15.0,
    )


def test_mobile_starts_without_data(
    monkeypatch,
    tmp_path,
):
    _isolated_state(
        monkeypatch,
        tmp_path,
    )

    status = mobile.mobile_status()

    assert status.state == "no_data"
    assert status.available is False
    assert status.node_id is None


def test_mobile_ingest_and_normalize(
    monkeypatch,
    tmp_path,
):
    _isolated_state(
        monkeypatch,
        tmp_path,
    )

    result = mobile.ingest_mobile_telemetry(
        {
            "node_id": "XPERION-SENSOR-01",
            "location": {
                "latitude": 49.99,
                "longitude": 8.27,
                "altitude_m": 101.5,
                "horizontal_accuracy_m": 3.4,
                "speed_mps": 0.2,
            },
            "heading": {
                "true_deg": 123.4,
                "magnetic_deg": 121.0,
            },
            "motion": {
                "attitude": {
                    "roll_rad": 0.1,
                }
            },
            "barometer": {
                "pressure_hpa": 1008.1,
            },
            "device": {
                "battery_percent": 73.0,
            },
        }
    )

    assert result["accepted"] is True

    status = mobile.mobile_status()

    assert status.state == "online"
    assert status.available is True
    assert status.node_id == "XPERION-SENSOR-01"

    assert status.latitude == 49.99
    assert status.longitude == 8.27
    assert status.altitude_m == 101.5

    assert status.horizontal_accuracy_m == 3.4
    assert status.heading_deg == 123.4
    assert status.speed_mps == 0.2

    assert "gnss" in status.capabilities
    assert "heading" in status.capabilities
    assert "imu" in status.capabilities
    assert "barometer" in status.capabilities
    assert "battery" in status.capabilities


def test_mobile_rejects_missing_node_id(
    monkeypatch,
    tmp_path,
):
    _isolated_state(
        monkeypatch,
        tmp_path,
    )

    try:
        mobile.ingest_mobile_telemetry(
            {
                "location": {
                    "latitude": 1.0,
                    "longitude": 2.0,
                }
            }
        )

    except mobile.MobileTelemetryError:
        return

    raise AssertionError(
        "Missing node_id was accepted."
    )

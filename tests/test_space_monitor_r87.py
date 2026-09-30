from core.space_monitor.normalization import (
    latest_kp,
    normalize_alerts,
    normalize_aurora,
    normalize_kp_forecast,
)


def test_latest_kp():
    rows = [
        {
            "time_tag": "2026-01-01T00:00:00Z",
            "Kp": "2.33",
        },
        {
            "time_tag": "2026-01-01T03:00:00Z",
            "Kp": "4.00",
        },
    ]

    kp, when = latest_kp(rows)

    assert kp == 4.0
    assert when == "2026-01-01T03:00:00Z"


def test_kp_forecast():
    rows = [
        {
            "time_tag": "2026-01-01T00:00:00Z",
            "kp": "5",
            "observed": "predicted",
            "noaa_scale": "G1",
        }
    ]

    result = normalize_kp_forecast(rows)

    assert result[0]["kp"] == 5.0
    assert result[0]["scale"] == "G1"


def test_alert_normalization():
    rows = [
        {
            "product_id": "TEST",
            "issue_datetime": "NOW",
            "message": "hello",
        }
    ]

    assert normalize_alerts(rows)[0]["product_id"] == "TEST"


def test_aurora_normalization():
    data = {
        "Observation Time": "A",
        "Forecast Time": "B",
        "coordinates": [[1, 2, 3]],
        "type": "Feature",
    }

    result = normalize_aurora(data)

    assert result["observation_time"] == "A"
    assert result["coordinates"] == [[1, 2, 3]]


def test_solar_wind_noaa_summary_shape():
    from core.space_monitor.normalization import (
        normalize_solar_wind,
    )

    speed = [
        {
            "proton_speed": 298,
            "time_tag": "2026-09-30T15:04:00Z",
        }
    ]

    mag = [
        {
            "bt": 4,
            "bz_gsm": 1,
            "time_tag": "2026-09-30T15:04:00Z",
        }
    ]

    propagated = [
        [
            "time_tag",
            "speed",
            "density",
            "temperature",
            "bx",
            "by",
            "bz",
            "bt",
            "vx",
            "vy",
            "vz",
            "propagated_time_tag",
        ],
        [
            "2026-09-30T14:10:00Z",
            296.5,
            3.6,
            57576.0,
            0.46,
            -2.79,
            2.89,
            4.04,
            -293.8,
            26.0,
            -30.6,
            "2026-09-30T15:28:04Z",
        ],
    ]

    result = normalize_solar_wind(
        propagated,
        speed,
        mag,
    )

    assert result["speed_km_s"] == 298.0
    assert result["magnetic_field_nt"] == 4.0
    assert result["bz_gsm_nt"] == 1.0
    assert result["density_p_cm3"] == 3.6

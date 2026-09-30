"""Marine R1 regression tests."""

from datetime import datetime, timezone

from core.marine.contracts import MarineObservation
from core.marine.freshness import age_seconds, classify
from core.marine.noaa_coops import NOAA_COOPS_Provider
from core.marine.service import MarineService


def test_freshness_uses_observation_age():
    observed = datetime(
        2026, 9, 29, 12, 0,
        tzinfo=timezone.utc,
    )
    received = datetime(
        2026, 9, 29, 12, 4,
        tzinfo=timezone.utc,
    )

    age = age_seconds(observed, received)

    assert age == 240
    assert classify("water_level", age) == "LIVE"


def test_contract_serialization():
    now = datetime(
        2026, 9, 29, 12, 0,
        tzinfo=timezone.utc,
    )

    item = MarineObservation(
        observation_id="fixture:1",
        kind="water_temperature",
        value=24.1,
        unit="degC",
        latitude=38.0,
        longitude=-76.0,
        observed_at=now,
        received_at=now,
        provider="fixture",
        freshness="LIVE",
        age_seconds=0,
    )

    payload = item.to_dict()

    assert payload["value"] == 24.1
    assert payload["data_mode"] == "OBSERVED"
    assert payload["observed_at"].endswith("Z")


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return b'''{
          "metadata": {
            "id": "TEST",
            "name": "Fixture Station",
            "lat": "38.000",
            "lon": "-76.000"
          },
          "data": [
            {
              "t": "2026-09-29 12:00",
              "v": "1.234",
              "q": "v"
            }
          ]
        }'''


def fake_open(request, timeout=0):
    return FakeResponse()


def test_noaa_coops_normalization():
    provider = NOAA_COOPS_Provider(
        opener=fake_open,
        clock=lambda: datetime(
            2026, 9, 29, 12, 4,
            tzinfo=timezone.utc,
        ),
    )

    rows = provider.observations(
        station="TEST",
        product="water_level",
    )

    assert len(rows) == 1

    row = rows[0]

    assert row.provider == "noaa_coops"
    assert row.station_id == "TEST"
    assert row.station_name == "Fixture Station"
    assert row.kind == "water_level"
    assert row.value == 1.234
    assert row.unit == "m"
    assert row.data_mode == "OBSERVED"
    assert row.age_seconds == 240
    assert row.freshness == "LIVE"
    assert row.latitude == 38.0
    assert row.longitude == -76.0
    assert row.quality == "v"


class FixtureProvider:
    provider_id = "fixture"

    def observations(
        self,
        *,
        station,
        product,
    ):
        now = datetime.now(timezone.utc)

        return [
            MarineObservation(
                observation_id=(
                    f"fixture:{station}:{product}"
                ),
                kind=product,
                value=1.0,
                unit="fixture",
                latitude=1.0,
                longitude=2.0,
                observed_at=now,
                received_at=now,
                provider=self.provider_id,
                station_id=station,
                freshness="LIVE",
                age_seconds=0,
            )
        ]


def test_service_aggregation():
    service = MarineService(
        providers=[FixtureProvider()]
    )

    payload = service.snapshot(
        station="ABC",
        products=["water_level"],
    )

    assert payload["operational_state"] == "LIVE"
    assert len(payload["observations"]) == 1
    assert payload["errors"] == []
    assert payload["sources"][0]["provider"] == "fixture"


def test_service_ready_without_station():
    service = MarineService(
        providers=[FixtureProvider()]
    )

    payload = service.snapshot()

    assert payload["operational_state"] == "READY"
    assert payload["observations"] == []
    assert payload["errors"] == []


def test_marine_route_is_in_openapi():
    from core.src.main import app

    paths = set(
        app.openapi()
        .get("paths", {})
        .keys()
    )

    assert "/environment/marine" in paths
    assert "/operations/sitrep" in paths
    assert "/health" in paths

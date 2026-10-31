from datetime import datetime, timezone
from pathlib import Path

from core.sitrep.service import SitrepService


class NuclearProvider:
    provider_id = "openstreetmap_nuclear_sites"
    publisher = "OpenStreetMap contributors"

    def __init__(self, fail=False):
        self.fail = fail

    def collect(self):
        if self.fail:
            raise RuntimeError("Simulated Overpass outage")

        return {
            "provider_id": self.provider_id,
            "publisher": self.publisher,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "sites": [{
                "id": "osm-test-1",
                "name": "Test facility",
                "location": {
                    "latitude": 40.0,
                    "longitude": 10.0,
                },
            }],
        }


def build_service(monkeypatch, path, fail=False):
    monkeypatch.setattr(
        SitrepService,
        "_nuclear_cache_path",
        lambda self: Path(path),
    )
    return SitrepService(
        providers=[NuclearProvider(fail=fail)],
    )


def test_successful_collection_creates_cache(tmp_path, monkeypatch):
    cache = tmp_path / "nuclear.json"
    service = build_service(monkeypatch, cache)

    snapshot = service.snapshot(force_refresh=True)

    assert snapshot["operational_state"] == "LIVE"
    assert cache.exists()
    assert len(snapshot["nuclear_sites"]) == 1


def test_cache_survives_restart(tmp_path, monkeypatch):
    cache = tmp_path / "nuclear.json"

    first = build_service(monkeypatch, cache)
    first.snapshot(force_refresh=True)

    second = build_service(
        monkeypatch,
        cache,
        fail=True,
    )

    snapshot = second.snapshot(force_refresh=True)

    assert snapshot["operational_state"] == "STALE"
    assert len(snapshot["nuclear_sites"]) == 1
    assert snapshot["sources"][0]["state"] == "STALE"


def test_invalid_cache_does_not_crash(tmp_path, monkeypatch):
    cache = tmp_path / "nuclear.json"
    cache.write_text("{invalid-json")

    service = build_service(
        monkeypatch,
        cache,
        fail=True,
    )

    snapshot = service.snapshot(force_refresh=True)

    assert snapshot["operational_state"] == "UNAVAILABLE"
    assert snapshot["nuclear_sites"] == []


def test_failed_collection_preserves_existing_cache(
    tmp_path, monkeypatch
):
    cache = tmp_path / "nuclear.json"

    first = build_service(monkeypatch, cache)
    first.snapshot(force_refresh=True)

    original = cache.read_bytes()

    second = build_service(
        monkeypatch,
        cache,
        fail=True,
    )

    second.snapshot(force_refresh=True)

    assert cache.read_bytes() == original

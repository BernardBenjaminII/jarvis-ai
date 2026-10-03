from __future__ import annotations

import json
import time

import pytest
import requests

from core.space_monitor import satellites


class FakeResponse:

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


SAMPLE = [
    {
        "OBJECT_NAME": "TEST SAT",
        "OBJECT_ID": "2026-001A",
        "EPOCH": "2026-10-02T20:00:00",
        "MEAN_MOTION": 15.0,
        "ECCENTRICITY": 0.001,
        "INCLINATION": 51.6,
        "RA_OF_ASC_NODE": 10.0,
        "ARG_OF_PERICENTER": 20.0,
        "MEAN_ANOMALY": 30.0,
        "NORAD_CAT_ID": 99999,
        "BSTAR": 0.0,
        "MEAN_MOTION_DOT": 0.0,
        "MEAN_MOTION_DDOT": 0.0,
    }
]


@pytest.fixture
def isolated_cache(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        satellites,
        "CACHE_DIR",
        tmp_path,
    )

    satellites._CACHE.clear()

    yield

    satellites._CACHE.clear()


def test_direct_celestrak_wins(
    isolated_cache,
    monkeypatch,
):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)

        assert url == satellites.BASE

        return FakeResponse(SAMPLE)

    monkeypatch.setattr(
        satellites.requests,
        "get",
        fake_get,
    )

    rows = satellites._fetch_group(
        "stations"
    )

    assert rows == SAMPLE
    assert calls == [satellites.BASE]

    assert satellites._cache_file(
        "stations"
    ).exists()


def test_mirror_used_after_direct_timeout(
    isolated_cache,
    monkeypatch,
):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)

        if url == satellites.BASE:
            raise requests.ConnectTimeout(
                "simulated direct timeout"
            )

        assert (
            url
            == f"{satellites.MIRROR_BASE}/stations.json"
        )

        return FakeResponse(SAMPLE)

    monkeypatch.setattr(
        satellites.requests,
        "get",
        fake_get,
    )

    rows = satellites._fetch_group(
        "stations"
    )

    assert rows == SAMPLE
    assert len(calls) == 2

    assert satellites._cache_file(
        "stations"
    ).exists()


def test_stale_disk_cache_used_when_both_fail(
    isolated_cache,
    monkeypatch,
):
    old = (
        time.time()
        - satellites.CACHE_TTL
        - 60
    )

    path = satellites._cache_file(
        "stations"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "fetched_at": old,
                "payload": SAMPLE,
            }
        )
    )

    def fail(*args, **kwargs):
        raise requests.ConnectTimeout(
            "simulated outage"
        )

    monkeypatch.setattr(
        satellites.requests,
        "get",
        fail,
    )

    rows = satellites._fetch_group(
        "stations"
    )

    assert rows == SAMPLE


def test_expired_disk_cache_does_not_hide_total_outage(
    isolated_cache,
    monkeypatch,
):
    old = (
        time.time()
        - satellites.STALE_CACHE_TTL
        - 60
    )

    path = satellites._cache_file(
        "stations"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "fetched_at": old,
                "payload": SAMPLE,
            }
        )
    )

    def fail(*args, **kwargs):
        raise requests.ConnectTimeout(
            "simulated outage"
        )

    monkeypatch.setattr(
        satellites.requests,
        "get",
        fail,
    )

    with pytest.raises(RuntimeError):
        satellites._fetch_group(
            "stations"
        )

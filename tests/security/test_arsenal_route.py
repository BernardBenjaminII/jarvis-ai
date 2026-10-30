import pytest
from fastapi import HTTPException

from core.src.routes import kali_arsenal


def test_kali_route_returns_inventory(monkeypatch):
    monkeypatch.setattr(
        kali_arsenal,
        "detect_platform",
        lambda: "kali",
    )

    monkeypatch.setattr(
        kali_arsenal,
        "build_arsenal_snapshot",
        lambda: {
            "health": "ready",
            "summary": {},
            "tools": [],
            "capabilities": [],
        },
    )

    payload = kali_arsenal.kali_arsenal()

    assert payload["platform"] == "kali"
    assert payload["inspection_mode"] == "static"
    assert payload["execution_authorized"] is False


def test_non_kali_route_fails_closed(monkeypatch):
    monkeypatch.setattr(
        kali_arsenal,
        "detect_platform",
        lambda: "ubuntu",
    )

    with pytest.raises(HTTPException) as exc:
        kali_arsenal.kali_arsenal()

    assert exc.value.status_code == 404

"""Tests for the JARVIS R2 RF control plane."""

from core.rf.manager import RFManager
from core.rf.models import RFTaskRequest


def test_rf_manager_starts_idle():
    manager = RFManager()

    status = manager.status()

    assert status.state == "idle"
    assert status.task is None


def test_rf_tasks_are_exposed():
    manager = RFManager()

    tasks = {
        item.id: item
        for item in manager.tasks()
    }

    assert "adsb" in tasks
    assert "fm" in tasks
    assert "rf_scan" in tasks
    assert "manual" in tasks


def test_profile_request_model():
    request = RFTaskRequest(
        task="adsb"
    )

    assert request.task == "adsb"
    assert request.sample_rate == 2_048_000


def test_rf_routes_in_openapi():
    from core.src.main import app

    paths = app.openapi()["paths"]

    assert "/api/rf/status" in paths
    assert "/api/rf/tasks" in paths
    assert "/api/rf/task/start" in paths
    assert "/api/rf/task/stop" in paths

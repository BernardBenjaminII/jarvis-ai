"""JARVIS receive-only RF task API."""

from __future__ import annotations

from fastapi import APIRouter

from core.rf import get_rf_manager
from core.rf.models import (
    RFStatus,
    RFTaskDescriptor,
    RFTaskRequest,
)


router = APIRouter(
    prefix="/api/rf",
    tags=["RF"],
)


@router.get(
    "/status",
    response_model=RFStatus,
)
def rf_status() -> RFStatus:
    return get_rf_manager().status()


@router.get(
    "/tasks",
    response_model=list[RFTaskDescriptor],
)
def rf_tasks() -> list[RFTaskDescriptor]:
    return get_rf_manager().tasks()


@router.post(
    "/task/start",
    response_model=RFStatus,
)
def rf_start(
    request: RFTaskRequest,
) -> RFStatus:
    return get_rf_manager().start(
        request
    )


@router.post(
    "/task/stop",
    response_model=RFStatus,
)
def rf_stop() -> RFStatus:
    return get_rf_manager().stop()

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from core.bootstrap.discovery.platform import detect_platform
from core.security.arsenal import build_arsenal_snapshot
from core.security import external_arsenal
from core.security.arsenal_search_r32 import indexed_search


router = APIRouter(
    prefix="/api/kali/arsenal",
    tags=["kali-arsenal"],
)


def _environment() -> str:
    detected = detect_platform()

    if isinstance(detected, str):
        return detected.strip().lower()

    if isinstance(detected, dict):
        return str(
            detected.get("environment")
            or detected.get("platform")
            or detected.get("distribution")
            or "unknown"
        ).strip().lower()

    return str(
        getattr(detected, "environment", "unknown")
    ).strip().lower()


@router.get("")
def kali_arsenal():
    environment = _environment()

    if environment != "kali":
        raise HTTPException(
            status_code=404,
            detail="Kali arsenal is not exposed on this platform.",
        )

    snapshot = build_arsenal_snapshot()

    return {
        "platform": environment,
        "execution_authorized": False,
        "inspection_mode": "static",
        **snapshot,
    }


@router.get("/")
def kali_arsenal_slash():
    return kali_arsenal()



@router.get("/external")
def external_arsenal_status():
    if _environment() != "kali":
        raise HTTPException(status_code=404)
    return external_arsenal.snapshot()


@router.get("/external/search")
def external_arsenal_search(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=30, ge=1, le=50),
):
    if _environment() != "kali":
        raise HTTPException(status_code=404)
    try:
        return indexed_search(q, limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


# JARVIS R9.19 R4: read-only workstation readiness.
@router.get("/workstation")
def kali_workstation_status():
    if _environment() != "kali":
        raise HTTPException(
            status_code=404,
            detail="Kali workstation is not exposed on this platform.",
        )

    from core.capabilities.kali_workstation import inventory_snapshot

    return inventory_snapshot()

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.bootstrap.discovery.platform import detect_platform
from core.security.arsenal import build_arsenal_snapshot


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

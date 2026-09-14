"""On-demand platform status for the UI; no polling or state mutation."""
from fastapi import APIRouter
from core.src.cognition.platform_status import snapshot

router = APIRouter()


@router.get("/api/runtime/platform")
def platform_status() -> dict:
    return snapshot()

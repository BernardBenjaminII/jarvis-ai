"""MC-1002 Commander's Bridge HTTP routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(tags=["Mission Control"])
STATIC_ROOT = Path(__file__).resolve().parents[1] / "static"
INDEX = STATIC_ROOT / "mission_control" / "index.html"
GLOBAL_3D_INDEX = STATIC_ROOT / "global_3d" / "index.html"


@router.get("/bridge", include_in_schema=False)
@router.get("/mission-control", include_in_schema=False)
def commanders_bridge() -> FileResponse:
    if not INDEX.is_file():
        raise HTTPException(503, "Mission Control is unavailable.")
    return FileResponse(INDEX, media_type="text/html", headers={"Cache-Control": "no-store"})


@router.get("/global-3d", include_in_schema=False)
def global_3d() -> FileResponse:
    """JARVIS Global 3D common operating picture."""
    if not GLOBAL_3D_INDEX.is_file():
        raise HTTPException(503, "Global 3D is unavailable.")
    return FileResponse(
        GLOBAL_3D_INDEX,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )

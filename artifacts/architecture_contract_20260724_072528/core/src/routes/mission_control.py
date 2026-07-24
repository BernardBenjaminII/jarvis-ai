"""MC-1002 Commander's Bridge HTTP routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(tags=["Mission Control"])
INDEX = Path(__file__).resolve().parents[1] / "static" / "mission_control" / "index.html"


@router.get("/bridge", include_in_schema=False)
@router.get("/mission-control", include_in_schema=False)
def commanders_bridge() -> FileResponse:
    if not INDEX.is_file():
        raise HTTPException(503, "Mission Control is unavailable.")
    return FileResponse(INDEX, media_type="text/html", headers={"Cache-Control": "no-store"})

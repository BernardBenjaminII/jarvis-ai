"""JARVIS FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.src.routes.api import router as api_router
from core.src.routes.mission_control import router as mission_control_router
from core.src.routes.operations import router as operations_router
from core.src.routes.executive_operations import (
    router as executive_operations_router,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_ROOT = BASE_DIR / "static"
MISSION_CONTROL_STATIC_ROOT = STATIC_ROOT / "mission_control"
LEGACY_UI_INDEX = STATIC_ROOT / "index.html"

app = FastAPI(title="JARVIS")


# ---------------------------------------------------------------------------
# Static assets
# ---------------------------------------------------------------------------

app.mount(
    "/mission-control/static",
    StaticFiles(directory=MISSION_CONTROL_STATIC_ROOT),
    name="mission-control-static",
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_ROOT),
    name="static",
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(mission_control_router)
app.include_router(operations_router)
app.include_router(executive_operations_router)
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Core application routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Redirect the root URL to Commander's Bridge."""

    return RedirectResponse(url="/bridge")


@app.get("/health")
def health() -> dict[str, str]:
    """Return the basic API process health state."""

    return {"status": "online"}


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def legacy_ui() -> FileResponse:
    """Serve the legacy JARVIS interface."""

    return FileResponse(
        LEGACY_UI_INDEX,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )

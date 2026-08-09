"""JARVIS FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.executive.events import (
    build_executive_event_runtime,
    executive_application_lifespan,
    resolve_operations_live_broker,
)
from core.src.routes.api import router as api_router
from core.src.routes.knowledge_workspace import router as knowledge_workspace_router
from core.src.routes.executive_event_runtime import (
    router as executive_event_runtime_router,
)
from core.src.routes.executive_operations import (
    router as executive_operations_router,
    runtime as operations_center_runtime,
)
from core.src.routes.mission_control import (
    router as mission_control_router,
)
from core.src.routes.operations import router as operations_router


BASE_DIR = Path(__file__).resolve().parent
STATIC_ROOT = BASE_DIR / "static"
MISSION_CONTROL_STATIC_ROOT = STATIC_ROOT / "mission_control"
LEGACY_UI_INDEX = STATIC_ROOT / "index.html"

executive_event_runtime = build_executive_event_runtime(
    live_broker=resolve_operations_live_broker(
        operations_center_runtime
    )
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with executive_application_lifespan(
        app,
        runtime=executive_event_runtime,
    ):
        yield


app = FastAPI(
    title="JARVIS",
    lifespan=lifespan,
)


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
#
# Route order is constitutional.
#
# Pack 2 established placeholder Executive Operations routes, including a
# temporary /operations/executive/events response. Pack 4A-3.1 establishes the
# event-runtime router as the authoritative owner of that path. FastAPI resolves
# duplicate paths in registration order, so the canonical router MUST precede
# the compatibility router.
# ---------------------------------------------------------------------------

app.include_router(mission_control_router)
app.include_router(operations_router)
app.include_router(executive_event_runtime_router)
app.include_router(executive_operations_router)
app.include_router(api_router)
app.include_router(knowledge_workspace_router)


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


@app.get(
    "/ui",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def legacy_ui() -> FileResponse:
    """Serve the legacy JARVIS interface."""
    return FileResponse(
        LEGACY_UI_INDEX,
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )

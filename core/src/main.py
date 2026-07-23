from pathlib import Path
from core.src.routes.mission_control import router as mission_control_router
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routes.api import router


app = FastAPI(title="JARVIS")
MISSION_CONTROL_STATIC_ROOT = Path(__file__).resolve().parent / "static" / "mission_control"
app.mount(
    "/mission-control/static",
    StaticFiles(directory=MISSION_CONTROL_STATIC_ROOT),
    name="mission-control-static",
)

# -----------------------------
# API ROUTES
# -----------------------------
app.include_router(mission_control_router)
app.include_router(observation_router)
app.include_router(reasoning_router)
app.include_router(knowledge_router)
app.include_router(mission_router)
app.include_router(operations_router)
app.include_router(router)

# -----------------------------
# STATIC FILES
# -----------------------------
app.mount(
    "/static",
    StaticFiles(directory="core/src/static"),
    name="static"
)


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/bridge")


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/health")
def health():
    return {
        "status": "online"
    }


# -----------------------------
# UI
# -----------------------------
@app.get("/ui", response_class=HTMLResponse)
def ui():

    with open("core/src/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# MC-1001 Operations Interface
try:
    from core.src.routes.operations import router as operations_router
except ModuleNotFoundError:
    from src.routes.operations import router as operations_router

app.include_router(operations_router)

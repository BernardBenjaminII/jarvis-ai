from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.routes.api import router


app = FastAPI(title="JARVIS")


# -----------------------------
# API ROUTES
# -----------------------------
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
    return RedirectResponse(url="/ui")


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

    with open("core/src/static/index.html", "r") as f:
        return f.read()

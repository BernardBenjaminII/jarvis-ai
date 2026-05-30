from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.routes.api import router

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.include_router(router)

@app.get("/")
def root():
    return {"status": "JARVIS Core Online"}

@app.get("/ui")
def ui():
    return FileResponse("src/static/index.html")

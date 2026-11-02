"""Public FM radio presets for JARVIS SDR-B."""

import json
from pathlib import Path
from threading import RLock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.rf.dual_controller import SECONDARY, get_dual_rf_controller
from core.rf.models import RFTaskRequest

router = APIRouter(prefix="/api/radio", tags=["Radio"])
CONFIG = Path(__file__).resolve().parents[3] / "config/radio/germany_rhein_main.json"
LOCK = RLock()


class TuneRequest(BaseModel):
    preset_id: str


def presets():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("receiver_serial") != SECONDARY:
        raise RuntimeError("Unexpected receiver serial")
    return data


@router.get("/presets")
def get_presets():
    return presets()


@router.get("/status")
def get_status():
    return get_dual_rf_controller().status(SECONDARY)


@router.post("/tune")
def tune(request: TuneRequest):
    with LOCK:
        selection = next(
            (p for p in presets()["presets"] if p["id"] == request.preset_id),
            None,
        )
        if selection is None:
            raise HTTPException(404, "Unknown preset")

        hz = selection["frequency_hz"]
        if selection["modulation"] != "fm" or not 87500000 <= hz <= 108000000:
            raise HTTPException(400, "Unsupported FM preset")

        controller = get_dual_rf_controller()
        current = controller.status(SECONDARY)["status"]

        if current["state"] != "idle":
            raise HTTPException(409, "SDR-B busy: stop current mission first")

        result = controller.start(
            SECONDARY,
            RFTaskRequest(
                task="fm",
                device_serial=SECONDARY,
                frequency_hz=hz,
                modulation="fm",
            ),
        )

        if result["status"]["state"] == "error":
            raise HTTPException(500, result["status"].get("detail") or "Radio error")

        return {"preset": selection, "receiver": result}


@router.post("/stop")
def stop():
    with LOCK:
        controller = get_dual_rf_controller()
        current = controller.status(SECONDARY)["status"]

        if current["state"] == "idle":
            return controller.status(SECONDARY)

        if current["task"] != "fm":
            raise HTTPException(409, "SDR-B is running another mission")

        return controller.stop(SECONDARY)

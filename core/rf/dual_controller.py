"""Process-local dual RTL-SDR orchestration; receive-only missions."""
from __future__ import annotations
import json
from pathlib import Path
from threading import RLock
from typing import Any

from .manager import RFManager, get_rf_manager
from .models import RFTaskRequest

PRIMARY = "86182997"
SECONDARY = "05370246"
REGISTRY = Path(__file__).resolve().parents[2] / "config/rf/receivers.json"

class DualRFController:
    def __init__(self, primary: RFManager | None = None, secondary: RFManager | None = None):
        self._lock = RLock()
        self._receivers = {
            PRIMARY: primary if primary is not None else get_rf_manager(),
            SECONDARY: secondary if secondary is not None else RFManager(),
        }
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["receivers"]
        if registry[PRIMARY]["role"] != "adsb_primary" or registry[SECONDARY]["role"] != "rf_multimission":
            raise ValueError("RF registry serial/role mismatch")
        self._registry = {s: dict(registry[s]) for s in self._receivers}

    def _get(self, serial: str) -> RFManager:
        try:
            return self._receivers[serial]
        except KeyError as e:
            raise ValueError("Unknown SDR serial") from e

    def status(self, serial: str | None = None) -> dict[str, Any]:
        with self._lock:
            if serial is not None:
                return {"serial": serial, "identity": self._registry[serial], "status": self._get(serial).status().model_dump()}
            return {"schema_id": "jarvis.rf.dual.r1", "receivers": [self.status(s) for s in (PRIMARY, SECONDARY)]}

    def start(self, serial: str, request: RFTaskRequest) -> dict[str, Any]:
        with self._lock:
            worker = self._get(serial)
            if request.device_serial not in (None, serial):
                raise ValueError("Request device_serial does not match receiver path")
            # Never allow old-style implicit device 0 selection.
            bound = request.model_copy(update={"device_serial": serial})
            result = worker.start(bound)
            return {"serial": serial, "status": result.model_dump()}

    def stop(self, serial: str) -> dict[str, Any]:
        with self._lock:
            return {"serial": serial, "status": self._get(serial).stop().model_dump()}

_dual: DualRFController | None = None
_dual_lock = RLock()

def get_dual_rf_controller() -> DualRFController:
    global _dual
    with _dual_lock:
        if _dual is None:
            _dual = DualRFController()
        return _dual

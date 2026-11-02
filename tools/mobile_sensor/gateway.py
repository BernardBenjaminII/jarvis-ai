#!/usr/bin/env python3

import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(os.getenv("JARVIS_MOBILE_SENSOR_PORT", "8765"))
TOKEN = os.getenv("JARVIS_MOBILE_SENSOR_TOKEN", "jarvis-dev-sensor")

STATE_DIR = Path("/tmp/jarvis_mobile_sensor")
STATE_DIR.mkdir(parents=True, exist_ok=True)

LATEST = STATE_DIR / "latest.json"
LOG = STATE_DIR / "telemetry.jsonl"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, body):
        data = json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "online",
                "service": "jarvis-mobile-sensor-gateway",
                "port": PORT,
                "time": utc_now(),
            })
            return

        if self.path == "/latest":
            if not LATEST.exists():
                self.send_json(404, {
                    "status": "waiting",
                    "detail": "No telemetry received yet."
                })
                return

            try:
                self.send_json(200, json.loads(LATEST.read_text()))
            except Exception as exc:
                self.send_json(500, {"error": str(exc)})
            return

        self.send_json(404, {"detail": "Not Found"})

    def do_POST(self):
        if self.path != "/telemetry":
            self.send_json(404, {"detail": "Not Found"})
            return

        supplied = self.headers.get("X-Jarvis-Token", "")
        if supplied != TOKEN:
            self.send_json(401, {"detail": "Invalid sensor token"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            payload = json.loads(raw)

            payload["_gateway"] = {
                "received_at": utc_now(),
                "received_unix": time.time(),
                "client": self.client_address[0],
            }

            rendered = json.dumps(payload, indent=2)
            LATEST.write_text(rendered)

            with LOG.open("a") as fh:
                fh.write(json.dumps(payload, separators=(",", ":")) + "\n")

            location = payload.get("location") or {}

            print(
                f"[sensor] "
                f"{payload.get('node_id', 'unknown')} "
                f"lat={location.get('latitude')} "
                f"lon={location.get('longitude')} "
                f"acc={location.get('horizontal_accuracy_m')}m"
            )

            self.send_json(200, {
                "accepted": True,
                "received_at": payload["_gateway"]["received_at"]
            })

        except Exception as exc:
            self.send_json(400, {
                "accepted": False,
                "error": str(exc)
            })

    def log_message(self, fmt, *args):
        pass


print(f"JARVIS Mobile Sensor Gateway")
print(f"Listening on http://{HOST}:{PORT}")
print(f"Health:   /health")
print(f"Telemetry /telemetry")
print(f"Latest:   /latest")

ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$ROOT"
"$PYTHON_BIN" -m dev.certification.repair_genesis_ix_a4_7_pack3
"$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from core.src.main import app
from core.src.routes.api import conversation_service
o=conversation_service.orchestrator; old=o.synthesis_handler
o.synthesis_handler=lambda prompt,*a,**k:"CERTIFIED"
try:
    conversation_service.ask("internal architecture of the Quantum Banana Warp Core Mk XII",mode="full",metadata={"request_id":"pack3","session_id":"pack3"})
finally:
    o.synthesis_handler=old
r=TestClient(app).get("/operations/executive/grounded-answer")
assert r.status_code==200,r.text
x=r.json(); assert x["available"] and x["state"]=="unknown" and x["rejected_evidence"]>=1 and x["recommended_action"]
print("[PASS] Live telemetry endpoint")
print("[PASS] Unknown state and acquisition guidance exposed")
PY

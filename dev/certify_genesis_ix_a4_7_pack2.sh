#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"

"${PYTHON_BIN}" -m dev.certification.repair_genesis_ix_a4_7_pack2

"${PYTHON_BIN}" - <<'PY'
from core.src.routes.api import conversation_service

orchestrator = conversation_service.orchestrator
original = orchestrator.synthesis_handler
capture = {"calls": 0, "prompt": ""}

def synthesis(prompt, *args, **kwargs):
    capture["calls"] += 1
    capture["prompt"] = str(prompt)
    return "CERTIFIED GROUNDED RESPONSE"

orchestrator.synthesis_handler = synthesis
try:
    conversation_service.ask(
        "internal architecture of the Quantum Banana Warp Core Mk XII",
        mode="full",
        metadata={
            "certification": "genesis_ix_a4_7_pack2",
            "request_id": "pack2-request",
            "session_id": "pack2-session",
        },
    )
finally:
    orchestrator.synthesis_handler = original

plan = getattr(orchestrator, "_last_grounded_answer_plan", None)
service = getattr(orchestrator, "grounded_answer_service", None)

assert service is not None
assert plan is not None
assert plan.state.value == "unknown"
assert plan.recommended_action
assert capture["calls"] == 1
assert "JARVIS KNOWLEDGE GROUNDING:" in capture["prompt"]
assert "JARVIS GROUNDED ANSWER CONTRACT:" in capture["prompt"]

print("[PASS] Runtime service attached")
print("[PASS] Grounded answer plan built")
print("[PASS] Existing grounding prompt preserved")
print("[PASS] Grounded answer contract reaches synthesis")
print("[PASS] Synthesis invoked exactly once")
PY

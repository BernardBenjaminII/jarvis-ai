#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

"${PYTHON_BIN}" -m \
  dev.certification.repair_genesis_ix_a4_7_pack2b

"${PYTHON_BIN}" - <<'PY'
from core.src.routes.api import conversation_service

orchestrator = conversation_service.orchestrator
original_handler = orchestrator.synthesis_handler
capture = {
    "calls": 0,
    "prompt": "",
}

def deterministic_synthesis(
    prompt,
    *args,
    **kwargs,
):
    capture["calls"] += 1
    capture["prompt"] = str(prompt)
    return "CERTIFIED GROUNDED RESPONSE"

orchestrator.synthesis_handler = deterministic_synthesis

try:
    response = conversation_service.ask(
        "internal architecture of the Quantum Banana Warp Core Mk XII",
        mode="full",
        metadata={
            "certification": "genesis_ix_a4_7_pack2b",
            "request_id": "pack2b-request",
            "session_id": "pack2b-session",
        },
    )
finally:
    orchestrator.synthesis_handler = original_handler

plan = getattr(
    orchestrator,
    "_last_grounded_answer_plan",
    None,
)
runtime_service = getattr(
    orchestrator,
    "grounded_answer_service",
    None,
)

assert runtime_service is not None
assert plan is not None
assert plan.state.value == "unknown"
assert plan.recommended_action
assert capture["calls"] == 1, capture
assert (
    capture["prompt"].count(
        "JARVIS GROUNDED ANSWER CONTRACT:"
    )
    == 1
)
assert (
    "JARVIS KNOWLEDGE GROUNDING:"
    in capture["prompt"]
)

print("[PASS] GroundedAnswerRuntimeService attached")
print("[PASS] GroundedAnswerPlan built")
print("[PASS] Existing grounding prompt preserved")
print("[PASS] Grounded-answer contract appended once")
print("[PASS] Synthesis invoked exactly once")
print("[PASS] Public conversation service remains callable")
PY

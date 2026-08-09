#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

"${PYTHON_BIN}" - <<'PY'
from core.conversation.grounded_answer import (
    GroundedAnswerExecutionRequest,
    GroundedAnswerRuntimeContext,
    GroundedAnswerRuntimeService,
)
from core.retrieval.qualification import QualificationResult

service = GroundedAnswerRuntimeService.create_default()
request = GroundedAnswerExecutionRequest(
    context=GroundedAnswerRuntimeContext(
        request_id="certification-request",
        session_id="certification-session",
        operator_input="Unknown certification question",
        metadata={"certification": "genesis_ix_a4_7_pack1"},
    ),
    qualification=QualificationResult(),
)

response = service.plan(request)

assert response.answer is None
assert response.synthesis_invoked is False
assert response.metadata["behavior_change"] is False
assert response.state == "unknown"
assert response.plan.recommended_action

print("[PASS] Canonical runtime context")
print("[PASS] Qualification-to-plan adapter")
print("[PASS] Stable response projection")
print("[PASS] Unknown-state acquisition guidance")
print("[PASS] No live conversation-path integration")
PY
